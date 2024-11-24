package edu.berkeley.cs.jqf.fuzz.util;

public class InitPkgUtil {
    public static void main(String[] args) {
        String libName = "com.google.guava:guava:32.1.2-jre";
        try {
            ProcessBuilder processBuilder = new ProcessBuilder("python3", "../llm-seed-generator/main.py", libName);

            processBuilder.inheritIO();
            Process process = processBuilder.start();
            try {
                process.waitFor();
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        } catch (Exception e) {
            System.out.println("Cannot initialize the jar package.");
            System.exit(1);
        }
        System.out.println("Have initialized the package: " + libName);
    }
}