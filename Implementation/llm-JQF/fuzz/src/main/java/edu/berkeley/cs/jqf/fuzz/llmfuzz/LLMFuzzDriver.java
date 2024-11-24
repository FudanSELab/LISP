package edu.berkeley.cs.jqf.fuzz.llmfuzz;

import edu.berkeley.cs.jqf.fuzz.junit.GuidedFuzzing;
import edu.berkeley.cs.jqf.fuzz.util.FileUtils;
import edu.berkeley.cs.jqf.fuzz.util.output.ResultInfo;
import edu.lisp.entity.json.MethodJson;
import org.apache.commons.lang3.tuple.Pair;
import org.apache.commons.lang3.tuple.Triple;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class LLMFuzzDriver {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: java " + LLMFuzzDriver.class + " TEST_LIB TEST_METHOD");
            System.exit(1);
        }

        String libName = args[0];
        System.setProperty("jqf.llm.libName", libName);
        Pair<String, ClassLoader> packageInfo = LLMFuzzGuidanceImpl.initPackage();

        List<String> signatureList = new ArrayList<>();
        if (System.getProperty("jqf.llm.inputFile") == null) {
            signatureList.add(args[1]);
        } else {
            String filePath = System.getProperty("jqf.llm.inputFile");
            signatureList = List.of(FileUtils.readFile(filePath).split("\n"));
        }

        for (String methodSignature : signatureList) {
            try {
                System.setProperty("jqf.llm.methodSignature", methodSignature);

                // Create the first-stage LLMFuzzGuidanceImpl & Run the Junit test
                MethodJson json;
                try {
                    json = LLMFuzzGuidanceImpl.buildMethodJson(methodSignature);
                } catch (Exception e) {
                    LLMFuzzGuidanceImpl.writeResult(new ResultInfo(methodSignature, 0, 0, 0, 0, 0.0, 0, 0, 0.0, "Soot parse failure."));
                    continue;
                }

                try {
                    LLMFuzzGuidanceImpl.initInputs();
                } catch (RuntimeException e) {
                    LLMFuzzGuidanceImpl.writeResult(new ResultInfo(methodSignature, 0, 0, 0, 0, 0.0, 0, 0, 0.0, e.getMessage()));
                    continue;
                }

                LLMFuzzGuidanceImpl guidance = new LLMFuzzGuidanceImpl();
                Pair<List<Pair<String, String>>, Set<String>> listStringPair = guidance.parseResult();
                int originOutputNumber = listStringPair.getLeft().size();
                listStringPair.getRight().add("import " + json.getClassName() + ";");
                String driverURL = null;
                while (!listStringPair.getLeft().isEmpty()) {
                    Triple<List<Pair<Integer, Integer>>, Map<Integer, String>, String> casesInterval = guidance.initDriver(methodSignature, listStringPair.getLeft(), listStringPair.getRight(), json);

                    int line = guidance.compileDriver(packageInfo.getLeft(), casesInterval.getRight());
                    if (line == 0) {
                        guidance.setCasesNum(listStringPair.getLeft().size());
                        driverURL = casesInterval.getRight();
                        break;
                    } else {
                        if (line < casesInterval.getLeft().get(0).getLeft()) {
                            String importInfo = casesInterval.getMiddle().get(line);
                            listStringPair.getRight().remove(importInfo);
                        } else {
                            for (int i = 0; i < casesInterval.getLeft().size(); i++) {
                                if (casesInterval.getLeft().get(i).getLeft() <= line && line <= casesInterval.getLeft().get(i).getRight()) {
                                    casesInterval.getLeft().remove(i);
                                    listStringPair.getLeft().remove(i);
                                    break;
                                }
                            }
                        }
                    }
                }

                if (guidance.casesNum == 0) {
                    LLMFuzzGuidanceImpl.writeResult(new ResultInfo(methodSignature, originOutputNumber, 0, 0, 0, 0.0, 0, 0, 0.0, "No valid input."));
                    continue;
                }

                if (driverURL != null) {
                    String pkgClassName = driverURL.split("examples/target/classes/")[1];
                    String testClass = pkgClassName.substring(0, pkgClassName.length() - 5).replaceAll("/", ".");
                    GuidedFuzzing.run(testClass, "runLLMFuzz", packageInfo.getRight(), guidance, System.out);
                } else {
                    LLMFuzzGuidanceImpl.writeResult(new ResultInfo(methodSignature, originOutputNumber, 0, 0, 0, 0.0, 0, 0, 0.0, "Cannot init driver."));
                    continue;
                }

                try {
                    ResultInfo info = guidance.displayStats(true);
                    info.setOriginCaseNum(originOutputNumber);
                    LLMFuzzGuidanceImpl.writeResult(info);
                } catch (RuntimeException e) {
                    e.printStackTrace();
                    LLMFuzzGuidanceImpl.writeResult(new ResultInfo(methodSignature, originOutputNumber, 0, 0, 0, 0.0, 0, 0, 0.0, e.getMessage()));
                }

            } catch (Exception e) {
                System.out.println("LLMFuzzDriver error: " + e.getMessage());
                e.printStackTrace();
            }
        }
    }
}
