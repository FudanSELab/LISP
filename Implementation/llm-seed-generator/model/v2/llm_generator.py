import json
import logging
import sys

from langchain.chat_models import ChatOpenAI
from langchain.chains import SequentialChain

from .chain.equivalence_partitioning import EquivalencePartitioningChain
from .chain.equivalence_partitioning_2 import EquivalencePartitioningDeeperChain
from .chain.input_understanding import InputUnderstandingChain
from .chain.input_understanding_non_ep import InputUnderstandingNonEPChain
from .chain.input_generation import InputGenerationChain
from .chain.input_generation_non_ep import InputGenerationNonEPChain
from .chain.input_non_understanding import InputNonUnderstandingChain
from .chain.basic_generation_non_ep import BasicGenerationNonEP

from config import *


class LLMGenerator:
    def __init__(self, gpt_version="gpt-3.5-turbo", temperature=0.0) -> None:
        llm = ChatOpenAI(model=gpt_version, temperature=temperature)
        self.equivalence_partitioning_chain = EquivalencePartitioningChain(llm)
        self.equivalence_partitioning_deeper_chain = EquivalencePartitioningDeeperChain(llm)
        self.input_understanding_chain = InputUnderstandingChain(llm)
        self.input_generation_chain = InputGenerationChain(llm)
        self.input_generation_chain_non_ep = InputGenerationNonEPChain(llm)
        self.input_understanding_chain_non_ep = InputUnderstandingNonEPChain(llm)
        self.input_non_understanding_chain = InputNonUnderstandingChain(llm)
        self.basic_generation_chain = BasicGenerationNonEP(llm)

    def generate(self, mg_dict, generate_times: int = 1):
        """
        Used to generate test cases via method graph
        :param generate_times: the times for generation
        :param mg_dict:  dict of the method graph
        :return a dict:
            key: equivalence partitioning results
            value: test cases of this partitioning
        """
        eq_classes = []
        for i in range(3):
            print(f"> Enter: Equivalence Partitioning")
            # Equivalent class division for the current method
            eq_classes = self.equivalence_partitioning_chain.run(mg_dict["code"])
            print(f"> Finish: Equivalence Partitioning")
            print(f"> Results: {eq_classes}")
            if len(eq_classes) != 0:
                break
        if len(eq_classes) == 0:
            print("No.101 EXIT!!!")
            sys.exit(101)

        print(f"> Enter: Input Generation")
        all_primitive = True
        for p_name in mg_dict["parameters"]:
            if len(mg_dict["nodes"][mg_dict["parameters"][p_name]]) != 0:
                if mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName") is None:
                    all_primitive = False
                    break
                else:
                    if len(mg_dict["nodes"][mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName")]) != 0:
                        all_primitive = False
                        break
        test_inputs = {}
        for i in range(generate_times):
            for cls in eq_classes:
                print(f"    > For: {cls}")
                # Code understanding and generation for different equivalence classes
                if all_primitive:
                    test_inputs[cls + str(i)] = self.input_generation_chain.run(mg_dict, cls)
                else:
                    test_inputs[cls + str(i)] = self.input_understanding_chain.run(cls, mg_dict)
        print(f"> Finish: Input Generation")
        print(f"> Results: {test_inputs}")
        checking = True
        for k, v in test_inputs.items():
            # for code in v['java']:
            #     if code.find('import ') != -1:
            #         print("No.102 EXIT!!!")
            #         sys.exit(102)
            if len(v['java']) != 0:
                checking = False
        if checking:
            print("No.103 EXIT!!!")
            sys.exit(103)
        return test_inputs

    def generate_with_calling(self, mg_dict, generate_times: int = 1):
        """
        Used to generate test cases via method graph
        :param generate_times: the times for generation
        :param mg_dict:  dict of the method graph
        :return a dict:
            key: equivalence partitioning results
            value: test cases of this partitioning
        """
        eq_classes = []
        for i in range(3):
            print(f"> Enter: Equivalence Partitioning")
            # Equivalent class division for the current method
            eq_classes = self.equivalence_partitioning_deeper_chain.run(mg_dict["code"], mg_dict['callingCode'])
            print(f"> Finish: Equivalence Partitioning")
            print(f"> Results: {eq_classes}")
            if len(eq_classes) != 0:
                break
        if len(eq_classes) == 0:
            print("No.101 EXIT!!!")
            sys.exit(101)

        print(f"> Enter: Input Generation")
        all_primitive = True
        for p_name in mg_dict["parameters"]:
            if len(mg_dict["nodes"][mg_dict["parameters"][p_name]]) != 0:
                if mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName") is None:
                    all_primitive = False
                    break
                else:
                    if len(mg_dict["nodes"][mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName")]) != 0:
                        all_primitive = False
                        break
        test_inputs = {}
        for i in range(generate_times):
            for cls in eq_classes:
                print(f"    > For: {cls}")
                # Code understanding and generation for different equivalence classes
                if all_primitive:
                    test_inputs[cls + str(i)] = self.input_generation_chain.run(mg_dict, cls)
                else:
                    test_inputs[cls + str(i)] = self.input_understanding_chain.run(cls, mg_dict)
        print(f"> Finish: Input Generation")
        print(f"> Results: {test_inputs}")
        checking = True
        for k, v in test_inputs.items():
            # for code in v['java']:
            #     if code.find('import ') != -1:
            #         print("No.102 EXIT!!!")
            #         sys.exit(102)
            if len(v['java']) != 0:
                checking = False
        if checking:
            print("No.103 EXIT!!!")
            sys.exit(103)
        return test_inputs

    def generate_non_ep(self, mg_dict, generate_times: int = 1):
        print(f"> Enter: Input Generation")
        all_primitive = True
        for p_name in mg_dict["parameters"]:
            if len(mg_dict["nodes"][mg_dict["parameters"][p_name]]) != 0:
                if mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName") is None:
                    all_primitive = False
                    break
                else:
                    if len(mg_dict["nodes"][
                               mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName")]) != 0:
                        all_primitive = False
                        break
        test_inputs = {}
        for i in range(generate_times):
            if all_primitive:
                test_inputs["result" + str(i)] = self.input_generation_chain_non_ep.run(mg_dict)
            else:
                test_inputs["result" + str(i)] = self.input_understanding_chain_non_ep.run(mg_dict)
            print(f"> Finish: Input Generation")
        print(f"> Results: {test_inputs}")
        return test_inputs

    def generate_non_understanding(self, mg_dict, generate_times: int = 1):
        print(f"> Enter: Equivalence Partitioning")
        eq_classes = self.equivalence_partitioning_chain.run(mg_dict["code"])
        print(f"> Finish: Equivalence Partitioning")
        print(f"> Results: {eq_classes}")

        print(f"> Enter: Input Generation")
        all_primitive = True
        for p_name in mg_dict["parameters"]:
            if len(mg_dict["nodes"][mg_dict["parameters"][p_name]]) != 0:
                if mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName") is None:
                    all_primitive = False
                    break
                else:
                    if len(mg_dict["nodes"][
                               mg_dict["nodes"][mg_dict["parameters"][p_name]].get("innerClassName")]) != 0:
                        all_primitive = False
                        break
        test_inputs = {}
        for i in range(generate_times):
            for cls in eq_classes:
                print(f"    > For: {cls}")
                if all_primitive:
                    test_inputs[cls + str(i)] = self.input_generation_chain.run(mg_dict, cls)
                else:
                    test_inputs[cls + str(i)] = self.input_non_understanding_chain.run(cls, mg_dict)
        print(f"> Finish: Input Generation")
        print(f"> Results: {test_inputs}")
        return test_inputs

    def generate_basic(self, mg_dict, generate_times: int = 1):
        test_inputs = {}
        for i in range(generate_times):
            test_inputs[i] = self.basic_generation_chain.run(mg_dict)
        print(f"> Finish: Input Generation")
        print(f"> Results: {test_inputs}")
        return test_inputs


if __name__ == "__main__":
    file = open("../../graph.json", "r")
    file_content = file.read()
    file.close()
    mg_dict = json.loads(file_content.replace("\n", ""))
    generator = LLMGenerator()

    generator.generate_non_ep(mg_dict)
