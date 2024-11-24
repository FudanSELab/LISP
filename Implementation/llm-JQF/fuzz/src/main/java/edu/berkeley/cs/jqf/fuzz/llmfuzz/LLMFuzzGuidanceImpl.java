package edu.berkeley.cs.jqf.fuzz.llmfuzz;

import edu.berkeley.cs.jqf.fuzz.guidance.GuidanceException;
import edu.berkeley.cs.jqf.fuzz.guidance.Result;
import edu.berkeley.cs.jqf.fuzz.util.Coverage;
import edu.berkeley.cs.jqf.fuzz.util.FileUtils;
import edu.berkeley.cs.jqf.fuzz.util.output.ExcelUtils;
import edu.berkeley.cs.jqf.fuzz.util.output.ResultInfo;
import edu.berkeley.cs.jqf.instrument.tracing.events.*;
import edu.lisp.config.Global;
import edu.lisp.entity.json.MethodJson;
import edu.lisp.service.ParseService;
import edu.lisp.utils.JsonUtils;
import janala.instrument.SnoopInstructionMethodAdapter;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.apache.commons.lang3.tuple.ImmutableTriple;
import org.apache.commons.lang3.tuple.Pair;
import org.apache.commons.lang3.tuple.Triple;
import org.junit.runners.model.FrameworkMethod;
import org.junit.runners.model.TestClass;
import soot.Type;
import soot.asm.AsmUtil;

import java.io.*;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import java.util.stream.Collectors;

import static edu.berkeley.cs.jqf.instrument.tracing.ThreadTracer.instructionMethod;

public class LLMFuzzGuidanceImpl implements LLMFuzzGuidance {

    /**
     * About coverage
     */
    protected Coverage runCoverage = new Coverage();
    protected Coverage totalCoverage = new Coverage();
    private final Map<Integer, String> branchDescCache = new HashMap<>();
    private final Set<String> branchesCoveredInCurrentRun = new HashSet<>(); // after run finished, clear it.
    private final Set<String> allBranchesCovered = new HashSet<>();
    protected File coverageFile = new File(".output/coverage_hash");

    /**
     * A system console, which is non-null only if STDOUT is a console.
     */
    protected final Console console = System.console();
    /**
     * Minimum amount of time (in millis) between two stats refreshes.
     */
    protected final long STATS_REFRESH_TIME_PERIOD = 300;
    /**
     * Time since this guidance instance was created.
     */
    protected Date startTime = new Date();
    /**
     * Time at last stats refresh.
     */
    protected Date lastRefreshTime = startTime;
    /**
     * The number of trials completed.
     */

    protected int numTrials = 0;
    /**
     * The number of valid inputs.
     */
    protected int numValid = 0;
    /**
     * The number of test cases.
     */
    protected int casesNum = 0;
    /**
     * The set of unique failures found so far.
     */
    protected HashMap<String, Long> uniqueFailures = new HashMap<>();
    private String className;
    private String methodName;
    private String methodJVMName;

    @Override
    public InputStream getInput() throws IllegalStateException, GuidanceException {
        return null;
    }

    public void setCasesNum(int casesNum) {
        this.casesNum = casesNum;
    }

    @Override
    public boolean hasInput() {
        return numTrials < casesNum;
    }

    @Override
    public void handleResult(Result result, Throwable error) throws GuidanceException {
        numTrials++;
        runCoverage.computeNewCoverage(totalCoverage);
        totalCoverage.updateBits(runCoverage);
        if (error == null)
            numValid++;
        else
            uniqueFailures.put(error.toString(), (long) numTrials);
        displayStats(false);

        // record and accumulate coverage
        try {
            PrintWriter pw = new PrintWriter(this.coverageFile);
            this.branchesCoveredInCurrentRun.forEach(pw::println);
            pw.close();
        } catch (FileNotFoundException e) {
            throw new GuidanceException(e);
        }
        this.allBranchesCovered.addAll(this.branchesCoveredInCurrentRun);
    }

    /**
     * See {@link edu.berkeley.cs.jqf.fuzz.repro.ReproGuidance#generateCallBack(Thread)}
     *
     * @param thread the thread whose events to handle
     * @return a callback to log code coverage or execution traces
     */
    @Override
    public Consumer<TraceEvent> generateCallBack(Thread thread) {
        return (e) -> {
            this.runCoverage.handleEvent(e);
            if (e instanceof BranchEvent) {
                BranchEvent be = (BranchEvent) e;
                int hash = be.getIid() * 31 + be.getArm();
                String info = this.branchDescCache.get(hash);
                if (info == null) {
                    info = String.format(
                            "(%09d) %s#%s%s:%d [%d]",
                            be.getIid(),
                            be.getContainingClass(),
                            be.getContainingMethodName(),
                            be.getContainingMethodDesc(),
                            be.getLineNumber(),
                            be.getArm());
                    this.branchDescCache.put(hash, info);
                }
                this.branchesCoveredInCurrentRun.add(info);
            } else if (e instanceof CallEvent) {
                CallEvent ce = (CallEvent) e;
                String info = this.branchDescCache.get(ce.getIid());
                if (info == null) {
                    info = String.format(
                            "(%09d) %s#%s%s:%d --> %s",
                            ce.getIid(),
                            ce.getContainingClass(),
                            ce.getContainingMethodName(),
                            ce.getContainingMethodDesc(),
                            ce.getLineNumber(),
                            ce.getInvokedMethodName());
                    this.branchDescCache.put(ce.getIid(), info);
                }
                this.branchesCoveredInCurrentRun.add(info);
            } else if (e instanceof AllocEvent) {
                AllocEvent ae = (AllocEvent) e;
                String info = this.branchDescCache.get(ae.getIid());
                if (info == null) {
                    info = String.format(
                            "(%09d) %s#%s%s:%d --> %s",
                            ae.getIid(),
                            ae.getContainingClass(),
                            ae.getContainingMethodName(),
                            ae.getContainingMethodDesc(),
                            ae.getLineNumber(),
                            ae.getSize());
                    this.branchDescCache.put(ae.getIid(), info);
                }
            } else if (e instanceof ReturnEvent) {
                ReturnEvent re = (ReturnEvent) e;
                String info = this.branchDescCache.get(re.getIid());
                if (info == null) {
                    info = String.format(
                            "(%09d) %s#%s%s:%d --> %s",
                            re.getIid(),
                            re.getContainingClass(),
                            re.getContainingMethodName(),
                            re.getContainingMethodDesc(),
                            re.getLineNumber(),
                            re.getFileName());
                    this.branchDescCache.put(re.getIid(), info);
                }
            }
        };
    }

    protected ResultInfo displayStats(boolean force) {
        Date now = new Date();
        long intervalMilliseconds = now.getTime() - lastRefreshTime.getTime();
        intervalMilliseconds = Math.max(1, intervalMilliseconds);
        if (intervalMilliseconds < STATS_REFRESH_TIME_PERIOD && !force) {
            return null;
        }
        lastRefreshTime = now;
        long elapsedMilliseconds = now.getTime() - startTime.getTime();
        elapsedMilliseconds = Math.max(1, elapsedMilliseconds);

        StringBuilder display = new StringBuilder();
        display.append("\033[2J").append("\033[H").append("Semantic Fuzzing with LLM\n--------------------------\n\n");
        String sign;
        if (System.getProperty("jqf.llm.methodSignature") != null) {
            sign = System.getProperty("jqf.llm.methodSignature");
            display.append("Test signature:       ").append(sign).append("\n");
        } else {
            throw new RuntimeException("Cannot find the method signature.");
        }
        display.append("Elapsed time:         ").append(millisToDuration(elapsedMilliseconds)).append("\n");
        display.append("Number of executions: ").append(numTrials).append(" (total ").append(casesNum).append(")\n");
        display.append("Valid inputs:         ").append(numValid).append(" (").append(String.format("%.2f", (numValid * 100.0 / numTrials))).append(")\n");
        display.append("Unique failures:      ").append(uniqueFailures.size()).append("\n");
        ResultInfo info = new ResultInfo();
        info.setSignature(sign);
        info.setCaseNum(casesNum);
        if (force) {
            if (methodJVMName == null) {
                for (String jvmName : instructionMethod.keySet()) {
                    if (isJVMName(jvmName, sign)) {
                        methodJVMName = jvmName;
                        break;
                    }
                }
                if (methodJVMName == null)
                    throw new RuntimeException("Cannot find the method signature in the instructionMethod.");
            }
            String[] split = methodJVMName.split("/");
            String pkgName = split[0] + "/" + split[1] + "/" + split[2];
            AtomicInteger totalBranchesCount = new AtomicInteger();
            instructionMethod.forEach((k, v) -> {
                if (k.startsWith(pkgName))
                    totalBranchesCount.addAndGet(v.size());
            });
            int totalAllBranches = (int) SnoopInstructionMethodAdapter.branchesMap.values().stream().filter(n -> n.startsWith(pkgName) && instructionMethod.containsKey(n)).count();
            double totalBranchesFraction = (double) totalBranchesCount.get() / totalAllBranches;
            info.setPkgCovered(totalBranchesCount.get());
            info.setPkgAllBranches(totalAllBranches);
            info.setPkgCoverage(totalBranchesFraction);


            System.out.println(instructionMethod.getOrDefault(methodJVMName, new HashSet<>()));
            int apiBranchesCount = instructionMethod.getOrDefault(methodJVMName, new HashSet<>()).size();
            int apiAllBranches = (int) SnoopInstructionMethodAdapter.branchesMap.values().stream().filter(n -> n.equals(methodJVMName)).count();
            if (apiAllBranches == 0)
                apiAllBranches = 1;
            double apiBranchesFraction = (double) apiBranchesCount / apiAllBranches;
            info.setApiCovered(apiBranchesCount);
            info.setApiAllBranches(apiAllBranches);
            info.setApiCoverage(apiBranchesFraction);

            display.append("API   Coverage:       ").append(apiBranchesCount).append(" branches (").append(String.format("%.2f", apiBranchesFraction * 100))
                    .append("%% of ").append(apiAllBranches).append(" branches)\n");
            display.append("Total Coverage:       ").append(totalBranchesCount.get()).append(" branches (").append(String.format("%.2f", totalBranchesFraction * 100))
                    .append("%% of ").append(totalAllBranches).append(" branches)\n");

            info.setUniqueError(uniqueFailures.entrySet().stream().map(e -> e.getValue() + ": " + e.getKey()).collect(Collectors.joining("\n\n")));
        }
        System.out.printf(display.toString());
        return info;
    }

    protected String millisToDuration(long millis) {
        long seconds = TimeUnit.MILLISECONDS.toSeconds(millis % TimeUnit.MINUTES.toMillis(1));
        long minutes = TimeUnit.MILLISECONDS.toMinutes(millis % TimeUnit.HOURS.toMillis(1));
        long hours = TimeUnit.MILLISECONDS.toHours(millis);
        String result = "";
        if (hours > 0) {
            result = hours + "h ";
        }
        if (hours > 0 || minutes > 0) {
            result += minutes + "m ";
        }
        result += seconds + "s";
        return result;
    }

    @Override
    public void run(TestClass testClass, FrameworkMethod method, Object[] args) throws Throwable {
        LLMFuzzGuidance.super.run(testClass, method, args);
    }

    @Override
    public void observeGeneratedArgs(Object[] args) {
        args[0] = numTrials;
    }

    public Set<String> getAllBranchesCovered() {
        return allBranchesCovered;
    }

    public static void writeResult(ResultInfo info) {
        ExcelUtils.write(System.getProperty("jqf.llm.libName"), info);
    }

    public static void writeNumber(int originNumber, int finalNumber) {
        ExcelUtils.write(System.getProperty("jqf.llm.libName"), System.getProperty("jqf.llm.methodSignature"), originNumber, finalNumber);
    }

    public static Pair<String, ClassLoader> initPackage() {
        String libName = System.getProperty("jqf.llm.libName");
        String jarPath = Global.downloadDependencies(libName);
        String[] jarArray = jarPath.split(":");
        URL[] urls = new URL[jarArray.length];
        for (int i = 0; i < jarArray.length; i++) {
            try {
                urls[i] = new File(jarArray[i]).toURI().toURL();
            } catch (MalformedURLException e) {
                throw new RuntimeException(e);
            }
        }
        URLClassLoader loader = new URLClassLoader(urls, ClassLoader.getSystemClassLoader());
        return new ImmutablePair<>(jarPath, loader);
    }

    public static boolean isJVMName(String jvmSig, String sig) {
        String[] split = jvmSig.split("#");
        String jvmClassName = split[0];
        String jvmDesc = split[1];
        String originClassName = AsmUtil.toQualifiedName(jvmClassName);
        int i1 = jvmDesc.indexOf("(");
        int i2 = jvmDesc.indexOf(")");
        String originMethodName = jvmDesc.substring(0, i1);
        String paramDesc = jvmDesc.substring(i1, i2 + 1);
        String originParams = AsmUtil.toJimpleDesc(paramDesc, com.google.common.base.Optional.absent()).stream().map(Type::toString).map(n -> n.substring(n.lastIndexOf(".") + 1)).collect(Collectors.joining(","));
        String originName = originClassName + "." + originMethodName + "(" + originParams + ")";
        return originName.equals(sig);
    }

    public static MethodJson buildMethodJson(String sign) {
        MethodJson methodJson = ParseService.parseHierarchy(sign);
        JsonUtils.writeObjectIntoFile(methodJson);
        return methodJson;
    }

    public static void initInputs() {
        boolean logGenerate = Boolean.getBoolean("jqf.llm.logGenerate");
        try {
            ArrayList<String> list = new ArrayList<>();
            list.add("python3.10");
            list.add("../llm-seed-generator/main.py");
            String skip = System.getProperty("jqf.llm.skip");
            if (skip != null)
                switch (skip) {
                    case "skipEP":
                        list.add("skipEP");
                        break;
                    case "skipUnder":
                        list.add("skipUnder");
                        break;
                    case "basic":
                        list.add("basic");
                        break;
                    case "deeper":
                        list.add("deeper");
                        break;
                }

            ProcessBuilder processBuilder = new ProcessBuilder(list);
            if (logGenerate)
                processBuilder.inheritIO();
            Process process = processBuilder.start();
            try {
                int code = process.waitFor();
                System.out.println("!!!Code: " + code);
                if (code != 0) {
                    if (code == 101) {
                        throw new RuntimeException("Cannot extract partitioning result.");
                    } else if (code == 102) {
                        throw new RuntimeException("Generation result label error.");
                    } else if (code == 103) {
                        throw new RuntimeException("Generation format error.");
                    } else if (code == 110) {
                        throw new RuntimeException("Cannot initiate class object.");
                    } else {
                        throw new RuntimeException("Unknown Error - Cannot generate Inputs.");
                    }
                }
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        } catch (IOException e) {
            throw new RuntimeException("IOException");
        }
        System.out.println("Have generated inputs.");
    }

    public Pair<List<Pair<String, String>>, Set<String>> parseResult() {
        String inputsInfo = FileUtils.readFile("../input_generator");
        String[] cases = inputsInfo.split("---------------");
        ArrayList<Pair<String, String>> left = new ArrayList<>();
        Set<String> right = new LinkedHashSet<>();
        for (String aCase : cases) {
            if (!aCase.contains("Part1:"))
                continue;
            int i1 = aCase.indexOf("Part1:");
            int i2 = aCase.indexOf("Part2:");
            int i3 = aCase.indexOf("Part3:");
            String part1 = aCase.substring(i1 + 6, i2 - 1);
            String part2 = aCase.substring(i2 + 6, i3 - 1);
            String[] part3 = aCase.substring(i3 + 6).split("\n");
            left.add(new ImmutablePair<>(part1, part2));
            right.addAll(Arrays.stream(part3).map(String::trim).collect(Collectors.toList()));
        }
        return new ImmutablePair<>(left, right);
    }

    public Triple<List<Pair<Integer, Integer>>, Map<Integer, String>, String> initDriver(String signature, List<Pair<String, String>> inputsInfo, Set<String> importsInfo, MethodJson methodJson) {
        String template = FileUtils.readFile("DriverTemplate.tmpl");
        className = signature.substring(0, signature.lastIndexOf('.'));
        methodName = signature.substring(signature.lastIndexOf('.') + 1, signature.indexOf('('));
//        String packageName = className.substring(0, className.lastIndexOf("."));
        template = template.replace("{package}", "package edu.lisp." + className.toLowerCase() + ";");
        int line = 3;
        Set<String> imports = new HashSet<>(Set.of("import edu.berkeley.cs.jqf.fuzz.Fuzz;", "import edu.berkeley.cs.jqf.fuzz.JQF;", "import edu.berkeley.cs.jqf.fuzz.llmfuzz.LLMFuzz;", "import org.junit.runner.RunWith;"));
        imports.addAll(importsInfo);
        HashMap<Integer, String> indexOfImport = new HashMap<>();
        StringBuilder importStatements = new StringBuilder();
        for (String anImport : imports) {
            importStatements.append(anImport).append("\n");
            indexOfImport.put(line++, anImport);
        }
        template = template.replace("{imports}", importStatements.deleteCharAt(importStatements.length() - 1));
        line += 11;
        StringBuilder call = new StringBuilder();
        for (int i = 0; i < inputsInfo.size(); i++) {
            call.append("case ").append(i).append(": llmInnerTest").append(i).append("(); break;");
        }
        template = template.replace("{call}", call.toString());
        ArrayList<Pair<Integer, Integer>> pairList = new ArrayList<>();
        StringBuilder cases = new StringBuilder();
        for (int i = 0; i < inputsInfo.size(); i++) {
            StringBuilder thisCase = new StringBuilder();
            thisCase.append("public void llmInnerTest").append(i).append("() {\n");
            thisCase.append(inputsInfo.get(i).getLeft()).append("\n");
            thisCase.append(inputsInfo.get(i).getRight()).append("\n");
            String simpleClassName = className.substring(className.lastIndexOf(".") + 1);
            if (methodJson.isStatic()) {
                thisCase.append(simpleClassName).append(".").append(methodName).append("(").append(String.join(", ", methodJson.getParameters().keySet())).append(");\n");
            } else {
                thisCase.append(Character.toLowerCase(simpleClassName.charAt(0))).append(simpleClassName.substring(1)).append(".").append(methodName).append("(").append(String.join(", ", methodJson.getParameters().keySet())).append(");\n");
            }
            pairList.add(new ImmutablePair<>(line, line + thisCase.toString().split("\n").length));
            line += 2 + thisCase.toString().split("\n").length;
            thisCase.append("}\n\n");
            cases.append(thisCase);
        }
        template = template.replace("{testcases}", cases.toString());
        String basePath = "examples/target/classes/";
        Path path = Path.of(basePath);
        String target = "edu.lisp." + className.toLowerCase();
        for (String s : target.split("\\.")) {
            path = path.resolve(s);
            if (!path.toFile().exists())
                path.toFile().mkdir();
        }
        int index = 0;
        File file;
        while (true) {
            file = path.resolve(methodName + index + ".java").toFile();
            if (!file.exists()) {
                template = template.replace("{testingClassName}", methodName + index);
                FileUtils.writeFile(file.getAbsolutePath(), template, false);
                break;
            }
            index++;
        }
        return new ImmutableTriple<>(pairList, indexOfImport, file.getAbsolutePath());
    }

    public int compileDriver(String jarPath, String driverURL) {
        boolean logGenerate = Boolean.getBoolean("jqf.llm.logGenerate");
        StringBuilder result = new StringBuilder();
        try {
            InputStream sh = new ProcessBuilder("bash", "scripts/classpath.sh").start().getInputStream();
            StringBuilder cp = new StringBuilder();
            byte[] b = new byte[8192];
            for (int n; (n = sh.read(b)) != -1; )
                cp.append(new String(b, 0, n));
            cp.deleteCharAt(cp.length() - 1);
            String classPath = ".:" + cp + ":" + jarPath;
            classPath = classPath.trim();

            ProcessBuilder processBuilder = new ProcessBuilder("javac", "-cp", classPath, driverURL);

            Process process = processBuilder.start();

            int code = process.waitFor();
            if (code == 0) {
                InputStream inputStream = process.getInputStream();
                BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream));
                String line;
                while ((line = bufferedReader.readLine()) != null)
                    result.append("\n").append(line);
                if (logGenerate) System.out.println(result);
                return 0;
            } else {
                InputStream inputStream = process.getErrorStream();
                BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream));
                String line;
                while ((line = bufferedReader.readLine()) != null)
                    result.append("\n").append(line);
                if (logGenerate) System.out.println(result);
                new File(driverURL).delete();
                int i1 = result.indexOf(".java:") + 6;
                int i2 = result.indexOf(":", i1);
                return Integer.parseInt(result.substring(i1, i2));
            }
        } catch (IOException | InterruptedException e) {
            throw new RuntimeException("Unknown Exception");
        }
    }
}