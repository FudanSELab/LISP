package edu.lisp.service;

import edu.lisp.config.Global;
import edu.lisp.entity.json.MethodJson;
import edu.lisp.entity.json.NodeJson;
import edu.lisp.utils.format.JDTMethodFormatter;
import edu.lisp.utils.format.SootMethodFormatter;
import org.eclipse.jdt.core.dom.MethodDeclaration;
import soot.*;
import soot.jimple.toolkits.callgraph.Edge;
import soot.util.Chain;

import java.util.*;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.stream.Collectors;

public class ParseService {

    private final static HashMap<String, NodeJson> handledTypes = new HashMap<>();
    private final static Queue<SootClass> handleQueue = new LinkedBlockingQueue<>();

    /**
     * This method is used for parsing hierarchy level type information
     * @param methodSignature the signature of the testing method
     *                        {className}.{methodName}({ParamTypes})
     */
    public static MethodJson parseHierarchy(String methodSignature) {
        SootMethod sootMethod = Global.SOOT_METHOD_MAP.get(methodSignature);
        MethodDeclaration md = Global.METHOD_DECL_MAP.get(methodSignature);
        if (sootMethod == null || md == null) {
            throw new RuntimeException("Cannot find method: " + methodSignature);
        }

        MethodJson mj = new MethodJson();
        mj.setReturnTypeName(sootMethod.getReturnType().toQuotedString()).setStatic(sootMethod.isStatic())
                .setClassName(sootMethod.getDeclaringClass().getName()).setMethodName(JDTMethodFormatter.getShortMethodSigWithVariableName(md))
                .setCode(JDTMethodFormatter.getShortMethodSigWithVariableName(md) + " " + md.getBody().toString());
        List<Type> parameterTypes = sootMethod.getParameterTypes();
        List<String> paramNames = JDTMethodFormatter.getParamNamesList(md);
        assert parameterTypes.size() == paramNames.size();
        mj.setParameters(new LinkedHashMap<>());
        for (int i = 0; i < parameterTypes.size(); i++)
            mj.getParameters().put(paramNames.get(i), parameterTypes.get(i).toString());

        for (Type type : parameterTypes) {
            SootClass sootClass = parseType(type);
            if (sootClass != null)
                handleQueue.add(sootClass);
        }
        if (!sootMethod.isStatic()) {
            handleQueue.add(sootMethod.getDeclaringClass());
        }
        while (!handleQueue.isEmpty()) {
            parseClassInfo(handleQueue.poll());
        }

        Iterator<Edge> edgeIterator = Global.OLD_CG.edgesOutOf(sootMethod);
        StringBuilder callingCode = new StringBuilder();
        HashSet<SootMethod> hasCalling = new HashSet<>();
        while (edgeIterator.hasNext()) {
            Edge edge = edgeIterator.next();
            SootMethod targetMethod = edge.tgt();
            if (targetMethod.isConcrete() && !hasCalling.contains(targetMethod)) {
                String targetMethodSignature = "";
                for (Map.Entry<String, SootMethod> entry : Global.SOOT_METHOD_MAP.entrySet()) {
                    if (entry.getValue().equals(targetMethod)) {
                        targetMethodSignature = entry.getKey();
                        break;
                    }
                }
                MethodDeclaration targetMd = Global.METHOD_DECL_MAP.get(targetMethodSignature);
                if (targetMd != null) {
                    callingCode.append(JDTMethodFormatter.getShortMethodSigWithVariableName(targetMd)).append(" ").append(md.getBody().toString()).append("\n");
                }
            }
            hasCalling.add(targetMethod);
        }
        mj.setCallingCode(callingCode.toString());

        mj.setNodes(handledTypes);
        return mj;
    }

    private static SootClass parseType(Type type) {
        if (type instanceof RefType) {
            return ((RefType) type).getSootClass();
        } else if (type instanceof ArrayType) {
            ArrayType arrayType = (ArrayType) type;
            Type baseType = arrayType.baseType;
            if (baseType instanceof PrimType) {
                handledTypes.put(arrayType.toString(), new NodeJson().setClassType("array")
                        .setInnerClassName(baseType.toQuotedString()).setDimension(arrayType.numDimensions));
            } else {
                handledTypes.put(arrayType.toString(), new NodeJson().setClassType("array")
                        .setInnerClassName(((RefType) baseType).getClassName()).setDimension(arrayType.numDimensions));
            }
            return parseType(baseType);
        }else if (type instanceof PrimType) {
            handledTypes.put(type.toQuotedString(), new NodeJson());
            return null;
        }
        return null;
    }

    private static void parseClassInfo(SootClass sootClass) {
        if (handledTypes.containsKey(sootClass.getName()))
            return;
        if (sootClass.isJavaLibraryClass()) {
            handledTypes.put(sootClass.getName(), new NodeJson());
            return;
        }

        if (sootClass.isInterface()) {
            List<SootClass> subInterfaces = Global.NEW_HIERARCHY.getDirectSubinterfacesOf(sootClass);
            handleQueue.addAll(subInterfaces);
            List<String> subInterfacesName = subInterfaces.stream().map(SootClass::getName).collect(Collectors.toList());

            List<SootClass> implementers = Global.NEW_HIERARCHY.getDirectImplementersOf(sootClass);
            handleQueue.addAll(implementers);
            List<String> implementersName = implementers.stream().map(SootClass::getName).collect(Collectors.toList());

            HashMap<String, String> fields = new HashMap<>();
            for (SootField field : sootClass.getFields()) {
                fields.put(field.getName(), field.getType().toString());
                SootClass sc = parseType(field.getType());
                if (sc != null)
                    handleQueue.add(sc);
            }
            handledTypes.put(sootClass.getName(), new NodeJson().setClassType("interface").setSubInterfaceName(subInterfacesName)
                    .setImplementedClassName(implementersName).setFields(fields));
        } else {
            String classType = sootClass.isAbstract() ? "abstract class" : "class";

            String superClassName = null;
            if (sootClass.getSuperclassUnsafe() != null) {
                superClassName = sootClass.getSuperclassUnsafe().getName();
                handleQueue.add(sootClass.getSuperclassUnsafe());
            }

            List<SootClass> subClasses = Global.NEW_HIERARCHY.getDirectSubclassesOf(sootClass);
            subClasses = subClasses.stream().filter(SootClass::isPublic).collect(Collectors.toList());
            handleQueue.addAll(subClasses);
            List<String> subClassesName = subClasses.stream().map(SootClass::getName).collect(Collectors.toList());

            Chain<SootClass> interfaces = sootClass.getInterfaces();
            handleQueue.addAll(interfaces);
            List<String> interfacesName = interfaces.stream().map(SootClass::getName).collect(Collectors.toList());

            HashMap<String, String> fields = new HashMap<>();
            for (SootField field : sootClass.getFields()) {
                fields.put(field.getName(), field.getType().toString());
                SootClass sc = parseType(field.getType());
                if (sc != null)
                    handleQueue.add(sc);
            }

            List<SootMethod> cons = sootClass.getMethods().stream().filter(c -> c.isConstructor() && c.isPublic()).collect(Collectors.toList());
            Map<String, LinkedHashMap<String, String>> constructors = new HashMap<>();
            cons.forEach(n -> {
                String key = n.getDeclaringClass().getName() + "." + SootMethodFormatter.getNameWithParams(n);
                MethodDeclaration declaration = Global.METHOD_DECL_MAP.get(key);
                if (declaration == null) {
                    if (n.getParameterCount() == 0) {
                        constructors.put(n.getDeclaringClass().getShortName() + "()", new LinkedHashMap<>());
                        return;
                    }
                    System.out.println("Cannot find constructor: " + key);
                    return;
                }

                List<Type> parameterTypes = n.getParameterTypes();
                List<String> paramNames = JDTMethodFormatter.getParamNamesList(declaration);
                assert parameterTypes.size() == paramNames.size();
                LinkedHashMap<String, String> map = new LinkedHashMap<>();
                for (int i = 0; i < parameterTypes.size(); i++) {
                    map.put(paramNames.get(i), parameterTypes.get(i).toString());
                    SootClass sc = parseType(parameterTypes.get(i));
                    if (sc != null)
                        handleQueue.add(sc);
                }
                constructors.put(JDTMethodFormatter.getShortMethodSigWithVariableName(declaration), map);
            });

            List<SootMethod> bu = sootClass.getMethods().stream().filter(n -> n.isStatic() && n.isPublic() && n.getReturnType().equals(n.getDeclaringClass().getType())).collect(Collectors.toList());
            Map<String, LinkedHashMap<String, String>> builders = new HashMap<>();
            bu.forEach(n -> {
                String key = n.getDeclaringClass().getName() + "." + SootMethodFormatter.getNameWithParams(n);
                MethodDeclaration declaration = Global.METHOD_DECL_MAP.get(key);
                if (declaration == null) {
                    System.out.println("Cannot find method: " + key + " in JDT");
                    return;
                }

                List<Type> parameterTypes = n.getParameterTypes();
                List<String> paramNames = JDTMethodFormatter.getParamNamesList(declaration);
                assert parameterTypes.size() == paramNames.size();
                LinkedHashMap<String, String> map = new LinkedHashMap<>();
                for (int i = 0; i < parameterTypes.size(); i++) {
                    map.put(paramNames.get(i), parameterTypes.get(i).toString());
                    SootClass sc = parseType(parameterTypes.get(i));
                    if (sc != null)
                        handleQueue.add(sc);
                }
                builders.put(JDTMethodFormatter.getShortMethodSigWithVariableName(declaration), map);
            });

            handledTypes.put(sootClass.getName(), new NodeJson().setClassType(classType).setSuperClassName(superClassName)
                    .setSubClassName(subClassesName).setInterfaces(interfacesName).setFields(fields)
                    .setConstructors(constructors).setBuilders(builders));
        }
    }

}