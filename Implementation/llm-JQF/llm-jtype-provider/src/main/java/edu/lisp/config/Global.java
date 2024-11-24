package edu.lisp.config;

import edu.lisp.utils.format.JDTMethodFormatter;
import org.eclipse.jdt.core.dom.MethodDeclaration;
import org.eclipse.jdt.core.dom.TypeDeclaration;
import scala.Tuple4;
import edu.lisp.utils.*;
import soot.Hierarchy;
import soot.Scene;
import soot.SootClass;
import soot.SootMethod;
import soot.jimple.toolkits.callgraph.CallGraph;

import java.io.File;
import java.util.*;

public class Global {
    public static Map<String, List<String>> NEW_CLASSMETHOD_MAP = new HashMap<>();
    public static Map<String, List<String>> NEW_OVERLOAD_MAP = new HashMap<>();
    public static CallGraph OLD_CG = null;
    public static Hierarchy NEW_HIERARCHY = null;
    public static Collection<TypeDeclaration> CLASS_DECLS = new ArrayList<>();
    public static final Map<String, TypeDeclaration> CLASS_DECL_MAP = new HashMap<>();
    public static Collection<SootClass> SOOT_CLASSES = new ArrayList<>();
    public static final HashMap<String, SootClass> SOOT_CLASS_MAP = new HashMap<>();
    public static Collection<SootMethod> SOOT_METHODS = new ArrayList<>();
    public static final HashMap<String, SootMethod> SOOT_METHOD_MAP = new HashMap<>();
    public static Collection<MethodDeclaration> METHOD_DECLS = new ArrayList<>();
    public static final HashMap<String, MethodDeclaration> METHOD_DECL_MAP = new HashMap<>();


    public static void init(List<String> jarPath, String projPath) {

        RetrieveUtils.getAllJavaFiles(projPath).stream()
                .map(JDTUtils::getCompilationUnit)
                .filter(JDTUtils::isCuHasPackageDecl)
                .map(JDTUtils::visitCu)
                .filter(JDTUtils::isCuHasTypeDecl)
                .forEach(visitor -> visitor.types.forEach(td -> {
                    String packageName = visitor.cu.getPackage().getName().toString();
                    String className = ClassUtils.getClassName(td);
                    String fullyClassName = ClassUtils.getFullyClassName(packageName, className);

                    if (td.getMethods().length > 0)
                        CLASS_DECL_MAP.put(fullyClassName, td);

                    for (MethodDeclaration md : td.getMethods()) {
                        String fullyMethodName = JDTMethodFormatter.getFullyMethodSig(
                                packageName, className, JDTMethodFormatter.getShortMethodSig(md));
                        METHOD_DECL_MAP.put(JDTMethodFormatter.fixInit(fullyMethodName), md);
                    }
                }));

        // class -> methods map
        Set<String> methods = METHOD_DECL_MAP.keySet();
        NEW_CLASSMETHOD_MAP = ClassUtils.makeClassMethodMap(methods);

        // method overload information
        NEW_OVERLOAD_MAP = JDTMethodFormatter.getOverloadMethodMap(METHOD_DECL_MAP.keySet());

        // call-graph
        SootUtils.prepare(jarPath);
        OLD_CG = SootUtils.getCallGraph(CLASS_DECL_MAP.keySet());
        // hierarchy
        // must be called after Soot prepare
        NEW_HIERARCHY = Scene.v().getActiveHierarchy();

        // array version
        SOOT_CLASSES = SOOT_CLASS_MAP.values();
        SOOT_METHODS = SOOT_METHOD_MAP.values();
        CLASS_DECLS = CLASS_DECL_MAP.values();
        METHOD_DECLS = METHOD_DECL_MAP.values();

        System.out.println("Initialization finished");
    }

    /**
     * The GAV format here is "group_id:artifact_id:version"
     * e.g. org.scalaz:scalaz-core_2.11:7.2.3
     *
     * @param jarGAV GAV of a jar, see {@link CoursierUtils#makeDependency(String)}
     */
    public static String downloadDependencies(String jarGAV) {
        Tuple4<List<String>, List<String>, List<String>, List<String>> results =
                CoursierUtils.downloadDependencies(List.of(jarGAV));
        List<String> foundSrcs = results._1();

        List<String> rootPkgPaths = ZipUtils.unzipSourceJars(foundSrcs);
        FileUtils.integrateFolders(System.getProperty("user.dir") + File.separator + ".decompiled_sources", rootPkgPaths);
        init(results._3(), System.getProperty("user.dir") + File.separator + ".decompiled_sources");

        StringBuilder sb = new StringBuilder();
        results._3().forEach(r -> sb.append(r).append(":"));
        return sb.deleteCharAt(sb.length() - 1).toString();
    }

}
