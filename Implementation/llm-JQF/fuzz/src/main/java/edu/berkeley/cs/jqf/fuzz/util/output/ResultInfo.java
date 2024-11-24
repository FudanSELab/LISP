package edu.berkeley.cs.jqf.fuzz.util.output;

import com.alibaba.excel.annotation.format.NumberFormat;
import lombok.*;


@Data
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode
public class ResultInfo {
    private String signature;
    private Integer originCaseNum;
    private Integer caseNum;
    private Integer apiCovered;
    private Integer apiAllBranches;
    private Double apiCoverage;
    private Integer pkgCovered;
    private Integer pkgAllBranches;
    private Double pkgCoverage;
    private String uniqueError;
    @Override
    public String toString() {
        return signature + " " + originCaseNum + " " + caseNum + " " + apiCovered + " " + apiAllBranches + " " + apiCoverage +
                " " + pkgCovered + " " + pkgAllBranches + " " + pkgCoverage + " " + uniqueError;
    }
}
