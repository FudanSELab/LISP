package edu.lisp.entity.json;

import com.alibaba.fastjson2.annotation.JSONField;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Accessors(chain = true)
public class NodeJson{
    @JSONField(ordinal = 1)
    private String classType;

    @JSONField(ordinal = 2)
    private String superClassName;
    @JSONField(ordinal = 3)
    private List<String> subClassName;

    // Soot Not implemented yet!
    @JSONField(ordinal = 4)
    private List<String> superInterfaceName;
    @JSONField(ordinal = 5)
    private List<String> subInterfaceName;

    @JSONField(ordinal = 6)
    private List<String> interfaces;
    @JSONField(ordinal = 7)
    private List<String> implementedClassName;

    @JSONField(ordinal = 8)
    private Map<String, String> fields;
    @JSONField(ordinal = 9)
    private Map<String, LinkedHashMap<String, String>> constructors;
    @JSONField(ordinal = 10)
    private Map<String, LinkedHashMap<String, String>> builders;

    @JSONField(ordinal = 11)
    private String innerClassName;
    @JSONField(ordinal = 12)
    private Integer dimension;
}

