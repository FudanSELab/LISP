package edu.lisp.utils;

import edu.lisp.config.Global;
import soot.G;
import soot.Scene;
import soot.SootClass;
import soot.SootMethod;
import soot.jimple.toolkits.callgraph.CHATransformer;
import soot.options.Options;
import soot.jimple.toolkits.callgraph.CallGraph;
import edu.lisp.utils.format.SootMethodFormatter;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

public class SootUtils {

    public static void prepare(List<String> jarPaths) {
        G.reset();

        Options.v().set_process_dir(jarPaths);
        Options.v().set_src_prec(Options.src_prec_java);
        Options.v().set_whole_program(true);
        Options.v().set_allow_phantom_refs(true);
        Options.v().set_verbose(true);
        Options.v().set_keep_line_number(true);
        Options.v().setPhaseOption("jb", "use-original-names:true");
        Options.v().setPhaseOption("cg", "all-reachable:true");
        Options.v().set_no_bodies_for_excluded(true);
        Options.v().set_app(true);
    }

    public static CallGraph getCallGraph(Collection<String> classes) {
        assert (Options.v().process_dir() != null);
        assert (Options.v().whole_program());
        assert (Options.v().allow_phantom_refs());
        assert (Options.v().verbose());

        List<SootMethod> entryPoints = loadEntryPoints(classes);
        Scene.v().setEntryPoints(entryPoints);
        Scene.v().loadNecessaryClasses();
        Scene.v().loadBasicClasses();
        CHATransformer.v().transform();
        return Scene.v().getCallGraph();
    }

    public static List<SootMethod> loadEntryPoints(Collection<String> classNames) {
        return classNames.stream().map(SootUtils::loadEntryPoints).reduce((prev, curr) -> {
            prev.addAll(curr);
            return prev;
        }).orElse(new ArrayList<>());
    }

    private static List<SootMethod> loadEntryPoints(String className) {
        List<SootMethod> entryPoints = new ArrayList<>();

        SootClass sootClass = Scene.v().loadClassAndSupport(className);
        sootClass.setApplicationClass();
        Scene.v().loadNecessaryClasses();
        Global.SOOT_CLASS_MAP.put(sootClass.getName(), sootClass);

        sootClass.getMethods().forEach(method -> {
            Global.SOOT_METHOD_MAP.put(className + "." + SootMethodFormatter.getNameWithParams(method), method);
            if (!method.isPrivate()) {
                try {
                    method.retrieveActiveBody();
                } catch (RuntimeException ignored) {
                }
                entryPoints.add(method);
            }
        });
        return entryPoints;
    }
}
