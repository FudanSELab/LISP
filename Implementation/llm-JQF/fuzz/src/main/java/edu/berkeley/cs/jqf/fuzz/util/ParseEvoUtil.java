package edu.berkeley.cs.jqf.fuzz.util;

import com.alibaba.excel.EasyExcel;
import edu.berkeley.cs.jqf.fuzz.util.output.ResultInfo;

import java.util.ArrayList;
import java.util.List;

public class ParseEvoUtil {
    private final static String FILE_NAME = "new/net_fortuna";

    public static void main(String[] args) {
        String result = FileUtils.readFile("result/" + FILE_NAME);
        String[] strings = result.split("\n");

        ArrayList<ResultInfo> infos = new ArrayList<>();
        for (String string : strings) {
            if (string.equals("")) continue;
            List<Integer> indexesOfSpace = indexOf(string);
            if (indexesOfSpace.size() == 0) {
                infos.get(infos.size() - 1).setUniqueError(infos.get(infos.size() - 1).getUniqueError() + string + "\n");
                continue;
            }
            String first = string.substring(0, indexesOfSpace.get(0));
            int caseNum;
            try {
                caseNum = Integer.parseInt(first);
            } catch (NumberFormatException e) {
                if (string.startsWith("net/fortuna")) {
                    infos.add(new ResultInfo(first, 0, 0, 0, 0, 0.0, 0, 0, 0.0, "Cannot generate inputs"));
                    continue;
                }
                infos.get(infos.size() - 1).setUniqueError(infos.get(infos.size() - 1).getUniqueError() + string + "\n");
                continue;
            }
            String signature = string.substring(indexesOfSpace.get(0) + 1, indexesOfSpace.get(1));
            Integer apiCovered = Integer.parseInt(string.substring(indexesOfSpace.get(1) + 1, indexesOfSpace.get(2)));
            Integer apiAllBranches = Integer.parseInt(string.substring(indexesOfSpace.get(2) + 1, indexesOfSpace.get(3)));
            Double apiCoverage = Double.parseDouble(string.substring(indexesOfSpace.get(3) + 1, indexesOfSpace.get(4)));
            Integer pkgCovered = Integer.parseInt(string.substring(indexesOfSpace.get(4) + 1, indexesOfSpace.get(5)));
            Integer pkgAllBranches = Integer.parseInt(string.substring(indexesOfSpace.get(5) + 1, indexesOfSpace.get(6)));
            Double pkgCoverage = Double.parseDouble(string.substring(indexesOfSpace.get(6) + 1, indexesOfSpace.get(7)));
            String error = string.substring(indexesOfSpace.get(7) + 1);
            ResultInfo info = new ResultInfo(signature, caseNum, caseNum, apiCovered, apiAllBranches, apiCoverage, pkgCovered, pkgAllBranches, pkgCoverage, error);
            infos.add(info);
        }
        EasyExcel.write("result/" + FILE_NAME + ".xlsx", ResultInfo.class).sheet("sheet1").doWrite(infos);
    }

    private static List<Integer> indexOf(String string) {
        ArrayList<Integer> list = new ArrayList<>();
        for (int i = 0; i < string.length(); i++) {
            if (string.charAt(i) == ' ')
                list.add(i);
        }
        return list;
    }
}
