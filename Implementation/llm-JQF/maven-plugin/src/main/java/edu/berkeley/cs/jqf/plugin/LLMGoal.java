/**
 * Now it seems that integrating Maven Plugin Goal is not a good way,
 * since I cannot instrument all the classes.
 */
package edu.berkeley.cs.jqf.plugin;

import edu.berkeley.cs.jqf.fuzz.junit.GuidedFuzzing;
import edu.berkeley.cs.jqf.fuzz.llmfuzz.LLMFuzzGuidance;
import edu.berkeley.cs.jqf.fuzz.llmfuzz.LLMFuzzGuidanceImpl;
import edu.berkeley.cs.jqf.instrument.InstrumentingClassLoader;
import org.apache.maven.artifact.DependencyResolutionRequiredException;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugin.MojoFailureException;
import org.apache.maven.plugin.logging.Log;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.project.MavenProject;
import org.junit.runner.Result;

import java.io.*;
import java.net.MalformedURLException;
import java.util.*;

@Mojo(name = "llm", requiresDependencyResolution = ResolutionScope.TEST)
public class LLMGoal extends AbstractMojo {

    @Parameter(defaultValue = "${project}", required = true, readonly = true)
    MavenProject project;

    @Parameter(property = "excludes")
    private String excludes;

    @Parameter(property = "includes")
    private String includes;

    @Parameter(property = "logCoverage")
    private String logCoverage;

    @Parameter(property = "objectStorageRoot", defaultValue = LLMFuzzGuidance.OBJECT_STORAGE)
    private String objectStorageRoot;

    @Parameter(property = "class", required = true)
    private String testClassName;

    @Parameter(property = "method", required = true)
    private String testMethod;

    @Parameter(property = "executeNum", defaultValue = "100")
    private String executeNum;

    @Parameter(property = "keepOriginObj")
    private String keepOriginObj;

    @Override
    public void execute() throws MojoExecutionException, MojoFailureException {
        ClassLoader loader;
        LLMFuzzGuidanceImpl guidance;
        PrintStream out = System.out;
        Log log = getLog();
        Result result;

        // Configure classes to instrument
        if (excludes != null) {
            System.setProperty("janala.excludes", excludes);
        }
        if (includes != null) {
            System.setProperty("janala.includes", includes);
        }

        try {
            List<String> classpathElements = project.getTestClasspathElements();
            loader = new InstrumentingClassLoader(
                    classpathElements.toArray(new String[0]),
                    getClass().getClassLoader());
        } catch (DependencyResolutionRequiredException|MalformedURLException e) {
            throw new MojoExecutionException("Could not get project classpath", e);
        }

        // If a coverage dump file was provided, enable logging via system property
        if (logCoverage != null) {
            System.setProperty("jqf.llm.logUniqueBranches", "true");
        }

        if (objectStorageRoot != null) {
            System.setProperty("jqf.llm.objectStorageRoot", objectStorageRoot);
        }

        if (executeNum != null) {
            System.setProperty("jqf.llm.executeNum", executeNum);
        }

        if (keepOriginObj != null) {
            System.setProperty("jqf.llm.keepOriginObj", "true");
        }

        try {
            // NOTICE: assign "null" to guidance here, expecting GuidedFuzzing#run to invoke
            // GuidedFuzzing.setGuidance, making guidance equals to "null".
            // TODO: current guidance is dummy. it maybe cause some unexpected errors, need more considerations.
            guidance = new LLMFuzzGuidanceImpl();
            System.out.println("I construct a guidance " + guidance + " in LLMGoal without FrameworkMethod");
            result = GuidedFuzzing.run(testClassName, testMethod, loader, guidance, out);
            System.out.println("run finished!");
        } catch (ClassNotFoundException e) {
            throw new MojoExecutionException("Could not load test class", e);
        } catch (IllegalArgumentException e) {
            throw new MojoExecutionException("Bad request", e);
        } catch (RuntimeException e) {
            throw new MojoExecutionException("Internal error", e);
        }

        // see also {@link ReproGoal#execute}
        // since I remove the default value of logCoverage, this branch is seldom reached now.
        if (this.logCoverage != null) {
            Set<String> coverageSet = guidance.getAllBranchesCovered();
            assert (coverageSet != null);
            SortedSet<String> sortedCoverage = new TreeSet<>(coverageSet);
            try (PrintWriter covOut = new PrintWriter(this.logCoverage)) {
                sortedCoverage.forEach(covOut::println);
            } catch (IOException e) {
                log.error("Could not dump coverage info.", e);
            }
        }

        if (!result.wasSuccessful()) {
            throw new MojoFailureException("Test case produces a failure.");
        }
    }
}
