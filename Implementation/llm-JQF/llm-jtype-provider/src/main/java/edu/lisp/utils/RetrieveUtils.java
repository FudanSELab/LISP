package edu.lisp.utils;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class RetrieveUtils {

    public static List<File> getAllJavaFiles(String path) {
        return getAllJavaFiles(new File(path), true);
    }

    public static List<File> getAllJavaFiles(File path, Boolean excludeTest) {
        List<File> res = getAllFilesMatchPattern(path, "^\\w+\\.java$");
        if (excludeTest)
            return res.stream().filter(RetrieveUtils::pruneJavaTestFile).collect(Collectors.toList());
        else
            return res;
    }

    public static boolean pruneJavaTestFile(String javaFilePath) {
        return pruneJavaTestFile(new File(javaFilePath));
    }

    public static boolean pruneJavaTestFile(File javaFile) {
        String fileName = javaFile.getName();
        if (fileName.contains("Test.java"))
            return false;
        String absName = javaFile.getAbsolutePath();
        return !absName.contains("src" + File.separator + "test");
    }

    public static List<File> getAllFilesMatchPattern(File path, String regex) {
        if (path.isFile()) return new ArrayList<>();
        List<File> qualifiedFiles = new ArrayList<>();
        for (File file : Objects.requireNonNull(path.listFiles())) {
            if (file.isFile()) {
                Pattern p = Pattern.compile(regex);
                Matcher m = p.matcher(file.getName());
                if (m.matches()) {
                    qualifiedFiles.add(file);
                }
            } else if (file.isDirectory()) {
                qualifiedFiles.addAll(getAllFilesMatchPattern(file, regex));
            }
        }
        return qualifiedFiles;
    }
}
