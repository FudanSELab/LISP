package edu.lisp.utils.format;

import edu.lisp.config.Global;
import edu.lisp.utils.ClassUtils;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jdt.core.dom.MethodDeclaration;
import org.eclipse.jdt.core.dom.SingleVariableDeclaration;

import java.util.*;

public class JDTMethodFormatter {

    public static String getFullyMethodSig(MethodDeclaration md) {
        CompilationUnit cu = (CompilationUnit) md.getRoot();
        String packageName = cu.getPackage().getName().toString();
        String className = ClassUtils.getClassName(ClassUtils.getTypeDecl(md));
        String shortMethodSig = getShortMethodSig(md);
        return getFullyMethodSig(packageName, className, shortMethodSig);
    }

    public static String getFullyMethodName(String packageName, String className, String methodName) {
        return packageName + "." + className + "." + methodName;
    }

    public static String getFullyMethodSig(String packageName, String className, String shortMethodSig) {
        return packageName + "." + className + "." + shortMethodSig;
    }

    public static String getShortMethodSig(MethodDeclaration m) {
        String name = m.getName().toString();
        String params = getParamsList(m);
        return removeBracket(name + "(" + params + ")");
    }

    public static String getShortMethodSigWithVariableName(MethodDeclaration m) {
        String name = m.getName().toString();
        String params = getParamsListWithVariableName(m);
        return removeBracket(name + "(" + params + ")");
    }

    public static String getParamsList(MethodDeclaration m) {
        StringBuilder sb = new StringBuilder();
        List params = m.parameters();
        for (int i = 0; i < params.size(); i++) {
            SingleVariableDeclaration param = (SingleVariableDeclaration) params.get(i);
            String paramType = param.getType().toString();
            String s = "." + paramType;
            if (paramType.length() == 1 && Global.CLASS_DECL_MAP.keySet().stream().noneMatch(n -> n.endsWith(s)))
                paramType = "Object";
            sb.append(paramType);
            if (param.isVarargs())
                sb.append("[]");
            if (i != params.size() - 1)
                sb.append(",");
        }
        return sb.toString();
    }

    public static String getParamsListWithVariableName(MethodDeclaration m) {
        StringBuilder sb = new StringBuilder();
        List params = m.parameters();
        Iterator iter = params.iterator();
        while (iter.hasNext()) {
            SingleVariableDeclaration param = (SingleVariableDeclaration) iter.next();
            String paramType = param.getType().toString();
            String paramName = param.getName().toString();
            if (param.isVarargs()) {
                paramType = paramType + "[]";
            }
            sb.append(paramType).append(" ").append(paramName);
            if (iter.hasNext())
                sb.append(", ");
        }
        return sb.toString();
    }

    public static List<String> getParamNamesList(MethodDeclaration m) {
        List params = m.parameters();
        Iterator iter = params.iterator();
        List<String> list = new ArrayList<>();
        while (iter.hasNext()) {
            SingleVariableDeclaration param = (SingleVariableDeclaration) iter.next();
            String paramName = param.getName().toString();
            list.add(paramName);
        }
        return list;
    }

    public static String fixInit(String methodName) {
        String[] parts = methodName.split("\\(");
        if (parts.length < 2)
            return methodName;
        String packageClassMethod = parts[0];
        String[] pcmParts = packageClassMethod.split("\\.");
        if (pcmParts.length < 2)
            return methodName;
        else {
            String className = pcmParts[pcmParts.length - 2];
            String shortMethodName = pcmParts[pcmParts.length - 1];
            if (className.equals(shortMethodName))
                return methodName.replace(shortMethodName + "(", "<init>(");
            else
                return methodName;
        }
    }

    public static String fixInit(String className, String methodName) {
        String[] parts = methodName.split("\\(");
        if (parts.length < 2)
            return methodName;
        String shortMethodName = parts[0];
        if (className.equals(shortMethodName))
            return methodName.replace(shortMethodName + "(", "<init>(");
        else
            return methodName;
    }

    public static Map<String, List<String>> getOverloadMethodMap(Collection<String> methodNames) {
        Map<String, List<String>> m = new HashMap<>();
        methodNames.forEach(name -> {
            int end = name.indexOf("(");
            if (end != -1) {
                // get package.class.method name
                String pcm = name.substring(0, end);
                if (!m.containsKey(pcm))
                    m.put(pcm, new ArrayList<>());
                m.get(pcm).add(name);
            }
        });
        return m;
    }

    public static String removeBracket(String s) {
        Stack<Integer> stack = new Stack<>();
        HashMap<Integer, Integer> pair = new HashMap<>();

        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == '<')
                stack.push(i);
            if (s.charAt(i) == '>') {
                if (stack.size() >= 2) {
                    stack.pop();
                    continue;
                }
                if (stack.isEmpty())
                    continue;
                pair.put(stack.pop(), i);
            }
        }

        StringBuilder sb = new StringBuilder();
        boolean isIgnore = false;
        int endIgnoreI = -1;
        for (int i = 0; i < s.length(); i++) {
            if (pair.containsKey(i)) {
                isIgnore = true;
                endIgnoreI = pair.get(i);
            }
            if (i == endIgnoreI) {
                isIgnore = false;
                continue;
            }
            if (isIgnore)
                continue;
            sb.append(s.charAt(i));
        }
        return sb.toString();
    }
}
