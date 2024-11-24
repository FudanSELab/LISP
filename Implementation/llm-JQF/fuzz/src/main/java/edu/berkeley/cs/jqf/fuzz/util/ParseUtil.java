package edu.berkeley.cs.jqf.fuzz.util;

import com.alibaba.excel.EasyExcel;
import edu.berkeley.cs.jqf.fuzz.util.output.ResultInfo;
import org.apache.commons.codec.binary.StringUtils;

import java.net.InetAddress;
import java.util.ArrayList;
import java.util.List;

public class ParseUtil {

    private final static String FILE_NAME = "sis-utility_new_deeper_3";
    public static void main (String[] args) {
        String result = FileUtils.readFile("result/" + FILE_NAME);
        String[] strings = result.split("\n");

        ArrayList<ResultInfo> infos = new ArrayList<>();
        for (String string : strings) {
            if (string.equals("")) continue;
            if (string.charAt(0) < '0' || string.charAt(0) > '9') {
                string += " ";
                List<Integer> indexesOfSpace = indexOf(string);
                for (int i = 0; i < indexesOfSpace.size() - 8; i++) {
                    try {
                        String signature = string.substring(0, indexesOfSpace.get(i));
                        Integer originInputsNum = Integer.parseInt(string.substring(indexesOfSpace.get(i) + 1, indexesOfSpace.get(i + 1)));
                        Integer inputsNum = Integer.parseInt(string.substring(indexesOfSpace.get(i + 1) + 1, indexesOfSpace.get(i + 2)));
                        Integer apiCovered = Integer.parseInt(string.substring(indexesOfSpace.get(i + 2) + 1, indexesOfSpace.get(i + 3)));
                        Integer apiAllBranches = Integer.parseInt(string.substring(indexesOfSpace.get(i + 3) + 1, indexesOfSpace.get(i + 4)));
                        Double apiCoverage = Double.parseDouble(string.substring(indexesOfSpace.get(i + 4) + 1, indexesOfSpace.get(i + 5)));
                        Integer pkgCovered = Integer.parseInt(string.substring(indexesOfSpace.get(i + 5) + 1, indexesOfSpace.get(i + 6)));
                        Integer pkgAllBranches = Integer.parseInt(string.substring(indexesOfSpace.get(i + 6) + 1, indexesOfSpace.get(i + 7)));
                        Double pkgCoverage = Double.parseDouble(string.substring(indexesOfSpace.get(i + 7) + 1, indexesOfSpace.get(i + 8)));
                        String failures = string.substring(indexesOfSpace.get(i + 8) + 1);
                        ResultInfo info = new ResultInfo(signature, originInputsNum, inputsNum, apiCovered, apiAllBranches, apiCoverage, pkgCovered, pkgAllBranches, pkgCoverage, failures);
                        infos.add(info);
                        break;
                    } catch (NumberFormatException ignored){
                    }
                }
            } else {
                ResultInfo info = infos.get(infos.size() - 1);
                if (info.getUniqueError().length() < 30000)
                    info.setUniqueError(info.getUniqueError() + string);
            }
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
