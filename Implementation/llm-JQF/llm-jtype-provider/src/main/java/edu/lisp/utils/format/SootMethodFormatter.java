package edu.lisp.utils.format;

import soot.SootMethod;
import soot.Type;

public class SootMethodFormatter {

    public static String getFullyQualifiedName(String packageName, String className, SootMethod m) {
        return packageName + "." + className + "." + getNameWithParams(m);
    }

    public static String getFullyQualifiedName(String pkgClasName, SootMethod m) {
        return pkgClasName + "." + getNameWithParams(m);
    }

    public static String getNameWithParams(SootMethod m) {
        String simpleName = m.getName();
        if (m.getDeclaringClass().isInnerClass() && simpleName.equals("<init>")) {
            String shortName = m.getDeclaringClass().getShortName();
            simpleName = shortName.substring(shortName.lastIndexOf("$") + 1);
        }
        String params = getParams(m);
        return simpleName + "(" + params + ")";
    }

    public static String getParams(SootMethod m) {
        if (m.getParameterCount() == 0) return "";
        return m.getParameterTypes().stream().map(s -> {
            String nameOfType = getNameOfType(s);
            return nameOfType.substring(nameOfType.lastIndexOf("$") + 1);
        }).reduce((prev, curr) -> prev + "," + curr).orElse("");
    }

    public static String getNameOfType(Type t) {
        String fullyTypeName = t.toString();
        int beg = fullyTypeName.lastIndexOf(".");
        return fullyTypeName.substring(beg + 1);
    }

}
