package edu.lisp.utils;

import edu.lisp.config.Global;
import org.eclipse.jdt.core.dom.Javadoc;
import org.eclipse.jdt.core.dom.MethodDeclaration;
import org.eclipse.jdt.core.dom.SimpleName;
import org.eclipse.jdt.core.dom.TagElement;
import org.junit.Test;
import soot.*;
import soot.jimple.ThrowStmt;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class ExceptionTests {
    @Test
    public void test() {

        String baseUrl = "exception_info/";
        String libName = "org.knowm.xchart:xchart:3.8.7";
        String simpleName = libName.substring(libName.indexOf(":") + 1, libName.lastIndexOf(":"));
        String[] sigs = FileUtils.readFile(baseUrl + simpleName + "_sign").split("\n");
        String[] exec = FileUtils.readFile(baseUrl + simpleName).split("\n");

        assert sigs.length == exec.length;

        Global.downloadDependencies(libName);
        int total = 0, filtered = 0;
        HashMap<String, Integer> map = new HashMap<>();
        int doc_num = 0, throw_num = 0, both_num = 0;
        for (int i = 0; i < sigs.length; i++) {
            String signature = sigs[i];
            System.out.println(signature);
            Set<String> javadoc = analysisJavaDoc(signature);
            Set<String> aThrow = analysisThrow(signature);
            HashSet<String> fact = extractExceptions(exec[i]);
            total += fact.size();
            Set<String> difference = difference(difference(fact, aThrow).stream().map(s -> s.substring(s.lastIndexOf(".") + 1)).collect(Collectors.toSet()), javadoc);
            filtered += difference.size();
            Set<String> doc = intersection(fact.stream().map(s -> s.substring(s.lastIndexOf(".") + 1)).collect(Collectors.toSet()), javadoc);
            Set<String> throw_ = intersection(fact, aThrow);
            Set<String> both = intersection(throw_.stream().map(s -> s.substring(s.lastIndexOf(".") + 1)).collect(Collectors.toSet()), doc);
            if (difference.size() > 0) {
                System.out.println(difference.size() + ": " + difference + "(" + signature + ")");
                for (String s : difference) {
                    if (map.containsKey(s)) {
                        map.put(s, map.get(s) + 1);
                    } else {
                        map.put(s, 1);
                    }
                }
            }
            doc_num += doc.size();
            throw_num += throw_.size();
            both_num += both.size();
        }
        System.out.println(map);
        System.out.println(total);
        System.out.println(filtered);
        System.out.println(doc_num + " | " + throw_num + " | " + both_num);

    }

    public static Set<String> analysisJavaDoc(String sign) {
        HashSet<String> exceptions = new HashSet<>();
        MethodDeclaration declaration = Global.METHOD_DECL_MAP.get(sign);
        Javadoc javadoc = declaration.getJavadoc();
        if (javadoc == null) return new HashSet<>();
        for (Object tagObj : declaration.getJavadoc().tags()) {
            TagElement tag = (TagElement) tagObj;
            if (TagElement.TAG_THROWS.equals(tag.getTagName()) || TagElement.TAG_EXCEPTION.equals(tag.getTagName())) {
                for (Object fragment : tag.fragments()) {
                    if (fragment.getClass() == SimpleName.class) {
                        SimpleName sn = (SimpleName) fragment;
                        String fullyQualifiedName = sn.getFullyQualifiedName();
                        exceptions.add(fullyQualifiedName);
                    }
                }
            }
        }
        return exceptions;
    }

    public static Set<String> analysisThrow(String sign) {
        SootMethod sootMethod = Global.SOOT_METHOD_MAP.get(sign);
        Set<String> exceptions = sootMethod.getExceptions().stream().map(SootClass::getName).collect(Collectors.toSet());
        Body body = sootMethod.retrieveActiveBody();
        for (Unit unit : body.getUnits()) {
            if (unit instanceof ThrowStmt) {
                ThrowStmt throwStmt = (ThrowStmt) unit;
                Value thrownException = throwStmt.getOp();
                exceptions.add(thrownException.getType().toString());
            }
        }
        return exceptions;
    }

    public HashSet<String> extractExceptions(String message) {
        HashSet<String> classNames = new HashSet<>();
        String regex = "\\b[a-zA-Z_][a-zA-Z0-9_]*(?:\\.[a-zA-Z_][a-zA-Z0-9_]+)*(?:\\.(?:[A-Z][a-zA-Z0-9]*Exception|[A-Z][a-zA-Z0-9]*Error))";
        Pattern pattern = Pattern.compile(regex);
        Matcher matcher = pattern.matcher(message);

        while (matcher.find()) {
            classNames.add(matcher.group());
        }

        return classNames;
    }

    public static <T> Set<T> difference(Set<T> set1, Set<T> set2) {
        Set<T> result = new HashSet<>(set1);
        result.removeAll(set2);
        return result;
    }

    public static <T> Set<T> intersection(Set<T> set1, Set<T> set2) {
        Set<T> result = new HashSet<>(set1);
        result.retainAll(set2);
        return result;
    }

}
