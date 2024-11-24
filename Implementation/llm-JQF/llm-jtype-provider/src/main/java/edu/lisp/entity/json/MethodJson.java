package edu.lisp.entity.json;

import com.alibaba.fastjson2.annotation.JSONField;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.LinkedHashMap;
import java.util.Map;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Accessors(chain = true)
public class MethodJson {
    @JSONField(ordinal = 1)
    private String returnTypeName;
    @JSONField(ordinal = 2)
    private boolean isStatic;
    @JSONField(ordinal = 3)
    private String className;
    @JSONField(ordinal = 4)
    private String methodName;
    @JSONField(ordinal = 5)
    private LinkedHashMap<String, String> parameters;
    @JSONField(ordinal = 6)
    private String code;
    @JSONField(ordinal = 7)
    private String callingCode;
    @JSONField(ordinal = 8)
    private Map<String, NodeJson> nodes;
}