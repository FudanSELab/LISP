package edu.berkeley.cs.jqf.fuzz.util.output;

import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.EasyExcelFactory;
import com.alibaba.excel.ExcelWriter;
import com.alibaba.excel.read.listener.PageReadListener;
import com.alibaba.excel.write.metadata.WriteSheet;
import edu.berkeley.cs.jqf.fuzz.util.FileUtils;

import java.io.File;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ExcelUtils{

    public static void write(String pkgName, String signature, int originNumber, int finalNumber) {
        pkgName = pkgName.substring(pkgName.indexOf(":") + 1, pkgName.lastIndexOf(":"));
        FileUtils.writeFile("result/" + pkgName + "_number", signature + " " + originNumber + " " + finalNumber + "\n", true);
    }

    public static void write(String pkgName, ResultInfo info) {
        pkgName = pkgName.substring(pkgName.indexOf(":") + 1, pkgName.lastIndexOf(":"));
        pkgName += "_new";
        pkgName = System.getProperty("jqf.llm.skip") == null ? pkgName : pkgName + "_" + System.getProperty("jqf.llm.skip");
//        writeExcel(pkgName, info);
        writeText(pkgName, info);
    }

    private static void writeExcel(String pkgName, ResultInfo info) {
        List<ResultInfo> resultInfos = read(pkgName);
        resultInfos.add(info);
        EasyExcel.write("result/" + pkgName + ".xlsx", ResultInfo.class).sheet("sheet1").doWrite(resultInfos);
    }

    private static void writeText(String pkgName, ResultInfo info) {
        FileUtils.writeFile("result/" + pkgName, info + "\n", true);
    }

    public static List<ResultInfo> read(String pkgName){
        ArrayList<ResultInfo> resultInfos = new ArrayList<>();
        if (new File("result/" + pkgName + ".xlsx").exists())
            EasyExcel.read("result/" + pkgName + ".xlsx", ResultInfo.class, new PageReadListener<ResultInfo>(resultInfos::addAll)).sheet().doRead();
        return resultInfos;
    }

    public static List<ResultInfo> read(Path path){
        ArrayList<ResultInfo> resultInfos = new ArrayList<>();
        if (path.toFile().exists())
            EasyExcel.read(path.toAbsolutePath().toString(), ResultInfo.class, new PageReadListener<ResultInfo>(resultInfos::addAll)).sheet().doRead();
        return resultInfos;
    }
}
