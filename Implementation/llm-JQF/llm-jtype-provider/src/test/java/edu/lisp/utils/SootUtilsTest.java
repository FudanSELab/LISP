package edu.lisp.utils;

import edu.lisp.config.Global;
import org.junit.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class SootUtilsTest {

    @Test
    public void testUtils() {
        Global.downloadDependencies("joda-time:joda-time:2.12.5");
//        MethodJson mj = ParseService.parseHierarchy("org.apache.commons.lang3.ClassUtils.wrappersToPrimitives(final Class<?>...)");
//        MethodJson mj = ParseService.parseHierarchy("org.jfree.chart.axis.CyclicNumberAxis.refreshTicksHorizontal(Graphics2D,Rectangle2D,RectangleEdge)");
//        JsonUtils.writeObjectIntoFile(mj);
    }

    @Test
    public void generateFunc() {
        Global.downloadDependencies("org.ocpsoft.prettytime:prettytime:5.0.7.Final");
        List<String> signs = new ArrayList<>();
        Global.SOOT_METHOD_MAP.forEach((k, v) -> {
            if (!k.contains("$") && !k.contains("()") && !k.contains("<clinit>") && !k.contains("<init>")) {
                if (v.getDeclaringClass().isPublic() && !v.getDeclaringClass().isAbstract() && !v.getDeclaringClass().isInterface() && v.isPublic()) {
                    if (k.startsWith("org.ocpsoft.prettytime"))
                        signs.add(k);
                }
            }
        });
        FileUtils.writeFile("sign_2", String.join("\n", signs), false);
    }
}