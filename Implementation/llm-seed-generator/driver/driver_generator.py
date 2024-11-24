"""
Run `python driver/driver_generator.py` directly to test my functions
"""
import json
import re
import sys

from typing import Dict

PRIMITIVE_TYPES = ["byte", "short", "int", "long", "float", "double", "boolean", "char",
                   "byte[]", "short[]", "int[]", "long[]", "float[]", "double[]", "boolean[]", "char[]",
                   "byte[][]", "short[][]", "int[][]", "long[][]", "float[][]", "double[][]", "boolean[][]", "char[][]"]


def extract_method_signature(method_sig: str) -> Dict:
    """
    :param: method_sig 就是入参之一，这个 method_sig 和一般程序分析中的 method signature
            有很大区别，是 jazzer 的格式："pkg.class::method(params-type-list)"
    """
    result = re.search(r"^([\w.]+)::([\w]+)\(([^)]*)\)$", method_sig)
    if result is None:
        raise RuntimeError(f"cannot match regex: {method_sig}")

    matched_contents = result.groups()
    if len(matched_contents) != 3:
        error_msg = "; ".join(
            map(
                lambda x: f"{matched_contents.index(x) + 1}. {x}",
                matched_contents)
        )
        raise RuntimeError(
            f"size ({len(matched_contents)}) of matched contents ({error_msg}) invalid")

    return {
        "class_name": result.group(1),
        "method_name": result.group(2),
        "param_types": result.group(3)
    }


def extract_parameter_names(java_signature):
    params_content = re.search(r'\((.*?)\)', java_signature)

    if not params_content:
        return []

    params_content = params_content.group(1)
    params = params_content.split(',')
    param_names = [param.split()[-1] for param in params]
    return param_names


def get_info_from_mg(method_sig: str, mg: Dict) -> Dict:
    """
    :param: method_sig 和上面那个函数一样
    :param: mg method_graph 是 jtype 的输出之一
    """
    method_sig_info = extract_method_signature(method_sig)
    method_name = method_sig_info["method_name"]
    class_name = method_sig_info["class_name"].split(".")[-1]

    param_dict = mg["parameters"]
    is_static = mg["static"]
    if is_static:
        imported_types = list(param_dict.values())
        # import class type
        imported_types.append(method_sig_info["class_name"])
        imported_types = [s[:s.index('[')] if '[' in s else s for s in imported_types]
        imported_types = [s for s in imported_types if '.' in s]
        imports = "\n".join(
            map(
                lambda typ: f"import {typ};",
                # set 去重
                set(filter(
                    lambda typ: typ.lower() not in PRIMITIVE_TYPES,
                    imported_types))
            )
        )
        parameters = re.search(r'\((.*?)\)', mg["methodName"]).group(1)
        arguments = ", ".join(extract_parameter_names(mg["methodName"]))
        call_stmt = f"{class_name}.{method_name}({arguments});"
    else:
        if len(param_dict) == 0:
            raise RuntimeError(f"{method_sig} is an instance method, but in method graph, parameters' size == 0")
        receiver_name = "llm" + class_name

        imported_types = list(param_dict.values())
        imported_types.append(method_sig_info["class_name"])  # append wrapper class
        imported_types = [s[:s.index('[')] if '[' in s else s for s in imported_types]
        imports = "\n".join(
            map(
                lambda typ: f"import {typ};",
                # set 去重
                set(filter(
                    lambda typ: typ.lower() not in PRIMITIVE_TYPES,
                    imported_types))
            )
        )
        new_param_dict = {receiver_name: method_sig_info["class_name"]}
        new_param_dict.update(param_dict)
        parameters = re.search(r'\((.*?)\)', mg["methodName"]).group(1)
        parameters += ", " + class_name + " " + receiver_name
        parameters = parameters.replace("...", "[]")
        arguments = ", ".join(extract_parameter_names(mg["methodName"]))
        call_stmt = f"{receiver_name}.{method_name}({arguments});"

    return {
        "imports": imports,
        "parameters": parameters,
        "call_stmt": call_stmt
    }


def generate_driver_file(driver_path: str,
                         format_info: Dict,
                         tmpl_path: str = "driver/LLMFuzzDriver.tmpl") -> str:
    """
    :param: driver_path 父目录必须存在，不负责创建父目录
    :param: format_info 来自 get_info_from_mg
    """
    if "imports" not in format_info or \
            "parameters" not in format_info or \
            "call_stmt" not in format_info:
        raise RuntimeError(f"format_info is invalid: {format_info}")

    with open(tmpl_path, "r") as f:
        tmpl = f.read()
    content = tmpl.format(
        imports=format_info["imports"],
        params=format_info["parameters"],
        call_stmt=format_info["call_stmt"])
    with open(driver_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    method_sig = "com.github.javaparser.Range::strictlyContains(Position)"
    mg = {'static': True, 'returnTypeName': 'boolean', 'methodName': 'boolean strictlyContains(Position position)',
          'parameters': {'position': 'com.github.javaparser.Position', 'haha': 'int'},
          'code': 'boolean strictlyContains(Position position){\n    return position.isAfter(begin) && position.isBefore(end);\n}',
          'nodes': {'com.github.javaparser.Position': {'classType': 'class', 'superClassName': 'java.lang.Object',
                                                       'subClassName': [], 'interfaces': ['java.lang.Comparable'],
                                                       'fields': {'FIRST_LINE': 'int', 'FIRST_COLUMN': 'int',
                                                                  'line': 'int', 'column': 'int',
                                                                  'ABSOLUTE_BEGIN_LINE': 'int',
                                                                  'ABSOLUTE_END_LINE': 'int',
                                                                  'HOME': 'com.github.javaparser.Position'},
                                                       'constructors': {
                                                           'Position(int line, int column)': {'line': 'int',
                                                                                              'column': 'int'}},
                                                       'builders': {
                                                           'Position pos(int line, int column)': {'line': 'int',
                                                                                                  'column': 'int'}}},
                    'java.lang.Object': {}, 'java.lang.Comparable': {}, 'int': {}}}
    format_info = get_info_from_mg(method_sig, mg)
    print(format_info)

    method_sig = "org.apache.commons.lang3.StringUtils::lastIndexOfIgnoreCase(final CharSequence, final CharSequence, int)"
    mg = {'static': True, 'returnTypeName': 'int',
          'methodName': 'int lastIndexOfIgnoreCase(final CharSequence str, final CharSequence searchStr, int startPos)',
          'parameters': {'str': 'java.lang.CharSequence', 'searchStr': 'java.lang.CharSequence', 'startPos': 'int'},
          'code': 'int lastIndexOfIgnoreCase(final CharSequence str, final CharSequence searchStr, int startPos){\n    if (str == null || searchStr == null) {\n        return INDEX_NOT_FOUND;\n    }\n    final int searchStrLength = searchStr.length();\n    final int strLength = str.length();\n    if (startPos > strLength - searchStrLength) {\n        startPos = strLength - searchStrLength;\n    }\n    if (startPos < 0) {\n        return INDEX_NOT_FOUND;\n    }\n    if (searchStrLength == 0) {\n        return startPos;\n    }\n    for (int i = startPos; i >= 0; i--) {\n        if (CharSequenceUtils.regionMatches(str, true, i, searchStr, 0, searchStrLength)) {\n            return i;\n        }\n    }\n    return INDEX_NOT_FOUND;\n}',
          'nodes': {'java.lang.CharSequence': {}, 'int': {}}}
    format_info = get_info_from_mg(method_sig, mg)
    print(format_info)
    generate_driver_file("LLMFuzzDriver.java", format_info)

    method_sig = "org.apache.commons.lang3.BitField::getValue(final int)"
    mg = {'static': False, 'returnTypeName': 'int', 'methodName': 'int getValue(final int holder)',
          'parameters': {'holder': 'int'},
          'code': 'int getValue(final int holder){\n    return getRawValue(holder) >> shiftCount;\n}',
          'nodes': {'int': {}}}
    format_info = get_info_from_mg(method_sig, mg)
    print(format_info)
