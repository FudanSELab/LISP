import json
import random
import sys
from queue import Queue
from typing import Dict

OBTAIN_ALL_PARAM_INFO = -1


def return_type(mg: dict) -> str:
    return mg["returnTypeName"]


def method_name(mg: dict) -> str:
    return mg["methodName"]


def code_block(mg: dict) -> str:
    return mg["code"]


def parameters(mg: dict, layer: int = OBTAIN_ALL_PARAM_INFO, max_sub_num: int = sys.maxsize) -> Dict[str, Dict]:
    """
    Used to get parameter information of method graph
    :param mg: a method graph
    :param layer: the layer this function would search.
                  -1 by default, means to obtain all types
    :param max_sub_num: maximum number of subclasses to be extracted
    :return: a dict:
        key: fully qualified name of type,
        value: a dict:
            key: the signature of constructor of this type
            value: a dict (key: param name, value: param type)
    """
    types: Dict[str, Dict] = {}
    q1, q2, current_layer = Queue(), Queue(), 0
    s = set()
    # initialize, q1 and q2 are both used to do bfs.
    # q1 is used to pop, while q2 is used to load types of new layer
    [q1.put_nowait(param_type) for (param_name, param_type) in mg["parameters"].items()]
    while not q1.empty():
        typ = q1.get_nowait()
        if typ in mg["nodes"]:

            t_node = mg["nodes"][typ]
            if typ not in s:
                s.add(typ)
                if not t_node:
                    # it means that it's a jdk-builtin type
                    types[typ] = types.get(typ, dict())
                    types[typ].update({"__is_jdk_type__": True})
                else:
                    types[typ] = types.get(typ, dict())
                    types[typ] = {**types[typ], "classType": t_node.get("classType")}
                    node = types[typ]
                    if t_node.get("classType") == "class":
                        node["constructors"] = node.get("constructors", dict())
                        node["constructors"] = {**node["constructors"],
                                                **t_node.get("constructors", dict())}
                    if t_node.get("subClassName"):
                        if current_layer < layer:
                            size = max_sub_num if len(t_node.get("subClassName")) > max_sub_num else len(
                                t_node.get("subClassName"))
                            node["subClassName"] = node.get("subClassName", dict())

                            # key = random.choice(list(t_node.get("subClassName")))
                            # node["subClassName"] = {**node["subClassName"], "subClass0": key}
                            # q2.put_nowait(key)

                            for subClass_t in t_node["subClassName"]:
                                size -= 1
                                if not types.get(subClass_t):
                                    node["subClassName"] = node.get("subClassName", dict())
                                    node["subClassName"] = {**node["subClassName"],
                                                            "subClass" + str(max_sub_num - size): subClass_t}
                                    q2.put_nowait(subClass_t)
                                if size == 0:
                                    break
                    if t_node.get("implementedClassName"):
                        if current_layer < layer:
                            size = max_sub_num if len(t_node.get("implementedClassName")) > max_sub_num else len(
                                t_node.get("implementedClassName"))
                            node["implementedClassName"] = node.get("implementedClassName", dict())

                            # key = random.choice(list(t_node.get("subClassName")))
                            # node["subClassName"] = {**node["subClassName"], "subClass0": key}
                            # q2.put_nowait(key)

                            for subInterface_t in t_node["implementedClassName"]:
                                size -= 1
                                if not types.get(subInterface_t):
                                    node["implementedClassName"] = node.get("implementedClassName", dict())
                                    node["implementedClassName"] = {**node["implementedClassName"],
                                                            "implementedClass" + str(max_sub_num - size): subInterface_t}
                                    q2.put_nowait(subInterface_t)
                                if size == 0:
                                    break
                    if t_node.get("subInterfaceName"):
                        if current_layer < layer:
                            size = max_sub_num if len(t_node.get("subInterfaceName")) > max_sub_num else len(
                                t_node.get("subInterfaceName"))
                            for sub_interface_t in t_node["subInterfaceName"]:
                                size -= 1
                                if not types.get(sub_interface_t):
                                    node["subInterfaceName"] = node.get("subInterfaceName", dict())
                                    node["subInterfaceName"] = {**node["subInterfaceName"],
                                                                "subInterface" + str(max_sub_num - size): sub_interface_t}
                                    q2.put_nowait(sub_interface_t)
                                if size == 0:
                                    break
                    if t_node.get("fields"):
                        for field_t in t_node["fields"].values():
                            q2.put_nowait(field_t)
                    if t_node.get("constructors"):
                        if t_node.get("classType") == "class":
                            for constructor_params in t_node["constructors"].values():
                                for param_t in constructor_params.values():
                                    q2.put_nowait(param_t)
        # since q1.get_nowait might pop the last element in queue,
        # to avoid jumping out this loop when q2 is not empty,
        # push all the elements of q2 into q1
        if q1.empty():
            if layer != OBTAIN_ALL_PARAM_INFO and current_layer >= layer:
                return types
            current_layer += 1
            while not q2.empty():
                q1.put_nowait(q2.get_nowait())
    return types


def parameter_info(mg: dict, layer: int = OBTAIN_ALL_PARAM_INFO, max_sub_num: int = sys.maxsize) -> str:
    """
    Used to compose the information of parameters
    :param max_sub_num: Maximum number of subsequent subclasses of a class
    :param mg: a method graph
    :param layer: the layer this function would search.
                  -1 by default, means to obtain all types
    :return: a str with parameter information
    """
    required_params = parameters(mg, layer=layer, max_sub_num=max_sub_num)
    print(required_params)
    result = ""
    for (typ, infos) in required_params.items():
        if "__is_jdk_type__" in infos and infos["__is_jdk_type__"]:
            result += f"  - {typ}: a jdk-builtin type or cannot be parsed\n"
        else:
            class_type = infos["classType"]
            result += f"  - {class_type}: {typ}\n"
            if infos.get("subClassName"):
                result += "    - Sub classes name:\n"
                for name in infos["subClassName"].values():
                    result += f"        - {name}\n"
            if infos.get("subInterfaceName"):
                result += "    - Implementation classes name:\n"
                for name in infos["subInterfaceName"].values():
                    result += f"        - {name}\n"
            if infos.get("constructors"):
                result += "    - Constructors:\n"
                for (signature, params) in infos["constructors"].items():
                    result += f"        - {signature}: {params}\n"
    return result


if __name__ == "__main__":
    file = open("../graph.json", "r")
    file_content = file.read()
    file.close()
    mg1 = json.loads(file_content.replace("\n", ""))
    result1 = parameter_info(mg1, layer=5, max_sub_num=3)
    print(result1)
