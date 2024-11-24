package edu.lisp.utils;

import org.eclipse.jdt.core.dom.ASTNode;
import org.eclipse.jdt.core.dom.AbstractTypeDeclaration;
import org.eclipse.jdt.core.dom.MethodDeclaration;

import java.util.*;

public class ClassUtils {

    public static String getFullyClassName(String packageName, String className) {
        return packageName + "." + className;
    }

    public static String getClassName(AbstractTypeDeclaration typeDeclaration) {
        StringBuilder sb = new StringBuilder();
        AbstractTypeDeclaration td = typeDeclaration;
        while (true) {
            String className = td.getName().toString();
            sb.insert(0, className + "$");
            if (td.isPackageMemberTypeDeclaration()) {
                sb = new StringBuilder(sb.substring(0, sb.length() - 1));
                return sb.toString();
            }
            if (!(td.getParent() instanceof AbstractTypeDeclaration))
                return null;
            td = (AbstractTypeDeclaration) td.getParent();
        }
    }

    public static AbstractTypeDeclaration getTypeDecl(MethodDeclaration md) {
        ASTNode current = md;
        while (true) {
            current = current.getParent();
            if (current == null)
                return null;
            if (current instanceof AbstractTypeDeclaration)
                return (AbstractTypeDeclaration) current;
        }
    }

    public static Map<String, List<String>> makeClassMethodMap(Collection<String> methods) {
        HashMap<String, List<String>> m = new HashMap<>();
        for (String method : methods) {
            if (!method.contains("("))
                break;
            int end = method.indexOf('(');
            String nameWithoutParams = method.substring(0, end);
            int beg = nameWithoutParams.lastIndexOf('.');
            String className = nameWithoutParams.substring(0, beg);
            if (!m.containsKey(className)) {
                m.put(className, new ArrayList<>());
            }
            if (m.get(className) != null)
                m.get(className).add(method);
        }
        return m;
    }
}
