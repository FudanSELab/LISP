package edu.lisp.utils;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONWriter;

public class JsonUtils {
    public static void writeObjectIntoFile(Object object) {
        String jsonString = JSON.toJSONString(object, JSONWriter.Feature.PrettyFormat);
        FileUtils.writeFile("graph.json", jsonString, false);
    }
}
