package edu.lisp.utils

import coursier._
import coursier.core.Publication
import coursier.error.ResolutionError
import coursier.util.Artifact
import org.slf4j.{Logger, LoggerFactory}

import scala.concurrent.ExecutionContext.Implicits.global
import scala.jdk.CollectionConverters._

object CoursierUtils {

  /**
   * default repositories to fetch *.jar
   */
  private val repositories = Seq(
    coursier.LocalRepositories.ivy2Local,
    Repositories.central
  )

  def makeDependencies(inputs: List[String]): List[Dependency] =
    inputs.map(makeDependency)

  /**
   * construct a {@link Dependency}
   *
   * @param input groupId, artifactId, version seperated by ":".
   *              e.g. org.scalaz:scalaz-core_2.11:7.2.3
   * @return a {@link Dependency}
   */
  def makeDependency(input: String): Dependency = {
    val segment = input.split(":")
    segment match {
      case Array(group_id: String, artifact_id: String, version: String) =>
        makeDependency(group_id, artifact_id, version)
      case _ => throw new IllegalArgumentException(
        s"input $input is not valid, because it cannot be split into 3 pieces")
    }
  }

  def makeDependency(
                      group_id: String,
                      artifact_id: String,
                      version: String
                    ): Dependency =
    Dependency(Module(Organization(group_id), ModuleName(artifact_id)), version)

  def resolveDependencies(
                             inputs: List[String]
                           ): Seq[(Dependency, Publication, Artifact)] =
    _resolveDependencies(makeDependencies(inputs))

  private def _resolveDependencies(
                           inputs: List[Dependency]
                         ): Seq[(Dependency, Publication, Artifact)] = {
    try {
      val resolution = Resolve()
        .addDependencies(inputs: _*)
        .addRepositories(CoursierUtils.repositories: _*)
        .run()
      resolution.dependencyArtifacts()
    } catch {
      case e: ResolutionError =>
        System.out.println(
          s"resolveDependencies cannot resolve dependencies" +
            s"you need provide those dependencies can be downloaded, see stacktrace:")
        e.printStackTrace()
        Seq()
      case _ => Seq()
    }
  }

  /**
   * Exposed API.
   *
   * Used to download dependencies & get to know which jar/src is available locally
   *
   * @param deps the format defined in {@link makeDependency}
   * @return 4 seq
   */
  def downloadDependencies(
                            deps: java.util.List[String]
                          ) = {
    val tuples = resolveDependencies(deps.asScala.toList)
    val src_set = downloadDepSources(deps.asScala.toList)
    val jar_set = downloadDepJars(deps.asScala.toList)

    def getFullName(dep: Dependency): String = {
      val group_id_segment = dep.module.organization.value.replace(".", java.io.File.separator)
      val artifact_id = dep.module.name.value
      val version = dep.version
      val sep = java.io.File.separator
      s"$group_id_segment${sep}$artifact_id${sep}$version"
    }

    val (found_srcs, not_found_srcs) = src_set.partition(s => tuples.exists {
      case (dep, _, _) => s.contains(getFullName(dep))
      case _ => false
    })
    val (found_jars, not_found_jars) = jar_set.partition(j => tuples.exists {
      case (dep, _, _) => j.contains(getFullName(dep))
      case _ => false
    })

    (
      found_srcs.asJava,
      not_found_srcs.asJava,
      found_jars.asJava,
      not_found_jars.asJava
    )
  }

  def downloadDepSources(deps: List[String]): Seq[String] =
    _downloadDependencies(deps, Seq(Classifier.sources))

  def downloadDepJars(deps: List[String]): Seq[String] =
    _downloadDependencies(deps, Seq())

  /**
   * Used to download all dependencies specified
   *
   * @param deps deps list, should be in reliance with the format defined in {@link makeDependency}
   * @return all the paths to corresponding jar file
   */
  private def _downloadDependencies(
                                     deps: List[String],
                                     classifiers: Seq[Classifier]
                                   ): Seq[String] = {
    val dependencies = makeDependencies(deps)
    try {
      val jar_files = Fetch()
        .addDependencies(dependencies: _*)
        .addRepositories(CoursierUtils.repositories: _*)
        .addClassifiers(classifiers: _*)
        .run()
      jar_files.map(f => f.getAbsolutePath)
    } catch {
      case e: ResolutionError =>
        System.out.println(
          s"_downloadDependencies cannot download dependencies" +
            s"maybe you need to provide those dependencies manually, see stacktrace:")
        e.printStackTrace()
        Seq()
      case _ => Seq()
    }
  }

}
