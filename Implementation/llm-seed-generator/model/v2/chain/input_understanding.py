import json
import re
import logging
from queue import Queue

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.chains import LLMChain
from langchain.schema import LLMResult
import util.mg_util

SYSTEM_MESSAGE_1 = """
You are an experienced tester. Now you are expected to understand the inputs of the provided API method.
You need to give only one explicit constructor, which needs to be present in the provided Dependent Types.
You don't need to consider the various scenarios, you just need to pick out the best constructor for the situation.
Your answer should start with "- Constructor: ", and can only be followed by one constructor.
"""

QUESTION_MESSAGE_1 = [
    ("human",
     "API Method: ```java {code}```\n\nParameter: {param}\n\nDependent Types: \n{deps}\n\nInput Specification: {spec}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_1 = [
    ("human",
     "API Method: ```java {code}```\n\nParameter: {param}\n\nDependent Types: {deps}\n\nInput Specification: {spec}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

SYSTEM_MESSAGE_2 = """
Next you need to further parse the parameters in this constructor method.
You need to give only one explicit constructor, which needs to be present in the provided Dependent Types.
You don't need to consider the various scenarios, you just need to pick out the best constructor for the situation.
Your answer should start with "- Constructor: ", and can only be followed by one constructor.
"""

QUESTION_MESSAGE_2 = [
    ("human",
     "Constructor: ```java {constructor}```\n\nInput Specification: {spec}\n\nParameter: {param}\n\nDependent Types: \n{deps}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_2 = [
    ("human",
     "Constructor: ```java {constructor}```\n\nInput Specification: {spec}\n\nParameter: {param}\n\nDependent Types: {deps}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

SYSTEM_MESSAGE_3 = """
Depend on the constructors you have understood before, now you are expected to write test inputs for the provided API method.
Your answer must contain two part, Part.1 is the code to instantiate the objects and Part.2 is the required import statements.
"""

QUESTION_MESSAGE_3 = [
    ("human",
     "API Method: ```java {code}```\n\nConstructor: \n{constructors}\n\nInput Specification: {spec}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_3 = [
    ("human",
     "API Method: ```java {code}```\n\nConstructor: {constructors}\n\nInput Specification: {spec}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

SYSTEM_MESSAGE_3_NON_STATIC = """
Depend on the constructors you have understood before，now you are expected to write test inputs for the provided API method.
However this method is a non-static method, so you also need to write the initialisation statement for the class object to achieve high coverage.
Your answer is able to contains a lot of examples. Every example has, and only has, three parts. 
Part.1 contains test inputs initialization statements. Part.2 contains complete class object initialization statements with all parameters. Part.3 is the required import statements.
"""

QUESTION_MESSAGE_3_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nParams Constructor: {constructors}\n\nClass Constructor: {cons}\n\nInput Specification: {spec}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_3_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nParams Constructor: {constructors}\n\nClass Constructor: {cons}\n\nInput Specification: {spec}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

EXAMPLES_1 = [
    {
        "code": """
    TokenRange withBegin(JavaToken begin) {
        return new TokenRange(assertNotNull(begin), end);
    }
    """, "param": """
    `begin`
""", "deps": """
- class: com.github.javaparser.JavaToken
    - Constructors:
        - JavaToken(int kind): {'kind': 'int'}
        - JavaToken(int kind, String text): {'kind': 'int', 'text': 'java.lang.String'}
        - JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken): {'previousToken': 'com.github.javaparser.JavaToken', 'kind': 'int', 'nextToken': 'com.github.javaparser.JavaToken', 'range': 'com.github.javaparser.Range', 'text': 'java.lang.String'}
""", "spec": """
    1. `begin`: is null
    """, "answer": """
Based on the specification, we should instantiate the parameter `begin`.
However, `begin` is null, we can choose any constructor.
Therefore we can choose the following constructor randomly to instantiate `comment`:

- Constructor:
    JavaToken(int kind): {'kind': 'int'}
"""
    }, {
        "code": """
boolean contains(Comment comment) {
    if (!comment.hasRange())
      return false; 
    Range commentRange = comment.getRange().get();
    for (Comment c : getComments()) {
      if (!c.hasRange())
        return false; 
      Range cRange = c.getRange().get();
      if (cRange.begin.equals(commentRange.begin) && cRange.end.line == commentRange.end.line && Math.abs(cRange.end.column - commentRange.end.column) < 2)
        return true; 
    } 
    return false;
}
""", "param": """
`comment`
""", "deps": """
- abstract class: com.github.javaparser.ast.comments.Comment
    - Sub classes name:
        - com.github.javaparser.ast.comments.BlockComment
- class: com.github.javaparser.ast.comments.BlockComment
    - Constructors:
        - BlockComment(String content): {'content': 'java.lang.String'}
        - BlockComment(TokenRange tokenRange, String content): {'tokenRange': 'com.github.javaparser.TokenRange', 'content': 'java.lang.String'}
        - BlockComment(): {}
""", "spec": """
1. `comment`: has a range, but the list of comments is empty
""", "answer": """
This time we should understand the parameter called `comment`. Based on the dependent types,
we have know that `comment` is a `Comment` type which is a abstract class, 
so we should instantiate it using its subclasses. According to the dependencies, we can find `BlockComment`
is its subclass. `BlockComment` has three constructors, we should choose one to reach the specification.
Because `comment` need to have a range, through reading the signatures of constructors, we can infer that
`TokenRange` can be used to set a range. Therefore we can choose the following constructor which has `TokenRange` type
parameter to instantiate `comment`:

- Constructor:
    BlockComment(TokenRange tokenRange, String content): {'tokenRange': 'com.github.javaparser.TokenRange', 'content': 'java.lang.String'}
"""
    }
]

EXAMPLES_2 = [
    {
        "constructor": """
JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken): {'previousToken': 'com.github.javaparser.JavaToken', 'kind': 'int', 'nextToken': 'com.github.javaparser.JavaToken', 'range': 'com.github.javaparser.Range', 'text': 'java.lang.String'}
    """, "param": """
    `range`
    """, "spec": """
    1. `begin`: is not null
    """, "deps": """
     - int: a jdk-builtin type or cannot be parsed
     - java.lang.String: a jdk-builtin type or cannot be parsed
     - class: com.github.javaparser.Range
         - Constructors:
             - Range(Position begin, Position end): {'end': 'com.github.javaparser.Position', 'begin': 'com.github.javaparser.Position'}
    """, "answer": """
Based on the specification you give before, we should instantiate the parameter `range` with positions.
Therefore we use following constructor to instantiate `range` via the dependant types:

- Constructor:
    Range(Position begin, Position end): {'end': 'com.github.javaparser.Position', 'begin': 'com.github.javaparser.Position'}
    """
    }, {
        "constructor": """
BlockComment(TokenRange tokenRange, String content): {'tokenRange': 'com.github.javaparser.TokenRange', 'content': 'java.lang.String'}
""", "param": """
`tokenRange`
""", "spec": """
1. `comment`: has a range, but the list of comments is empty
""", "deps": """
- class: com.github.javaparser.TokenRange
    - Constructors:
        - TokenRange(JavaToken begin, JavaToken end): {'end': 'com.github.javaparser.JavaToken', 'begin': 'com.github.javaparser.JavaToken'}
- java.lang.String: a jdk-builtin type or cannot be parsed
""", "answer": """
Based on the specification you give before, we should use this constructor to set a range for `comment`.
According to analyse the parameters, we can infer that `tokenRange` is used to set a range. Therefore we use following
constructor to instantiate `tokenRange` via the dependant types:

- Constructor:
    TokenRange(JavaToken begin, JavaToken end): {'end': 'com.github.javaparser.JavaToken', 'begin': 'com.github.javaparser.JavaToken'}
"""
    }
]

EXAMPLES_3 = [
    {
        "code": """
boolean areInOrder(Node a, Node b, boolean ignoringAnnotations) {
    return compare(a, b, ignoringAnnotations) <= 0;
}
""", "constructors": """
Sub class of com.github.javaparser.ast.Node: com.github.javaparser.ast.type.UnknownType;
Constructor of com.github.javaparser.ast.type.UnknownType: UnknownType(TokenRange tokenRange): {'tokenRange': 'com.github.javaparser.TokenRange'}
Constructor of com.github.javaparser.TokenRange: TokenRange(JavaToken begin, JavaToken end): {'end': 'com.github.javaparser.JavaToken', 'begin': 'com.github.javaparser.JavaToken'}
Constructor of com.github.javaparser.JavaToken: JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken): {'previousToken': 'com.github.javaparser.JavaToken', 'kind': 'int', 'nextToken': 'com.github.javaparser.JavaToken', 'range': 'com.github.javaparser.Range', 'text': 'java.lang.String'}
Constructor of com.github.javaparser.Range: Range(Position begin, Position end): {'end': 'com.github.javaparser.Position', 'begin': 'com.github.javaparser.Position'}
Constructor of com.github.javaparser.Position: Position(int line, int column): {'line': 'int', 'column': 'int'}
""", "spec": """
1. `a`: is not null; 2. `b`: is not null, `a` is in order before `b`; 3. `ignoringAnnotations`: is true
""", "answer": """
Based on the constructors I have understood before, we can instantiate the parameter `a`, `b` and `ignoringAnnotations`.
According to the constructors, it is easy to specify a range. 
`com.github.javaparser.ast.Node` can be instantiated via its subclasses "com.github.javaparser.ast.type.UnknownType".
"UnknownType(TokenRange tokenRange)" can specify a range for `comment`.
Then we can use "TokenRange(JavaToken begin, JavaToken end", "JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken)",
"Range(Position begin, Position end)", "Position(int line, int column)" to instantiate hierarchically.
Because `a` is in order before `b`, `a`'s position should before `b`. Therefore, `Position(int line, int column)` can be used to specify the line and column numbers of `a` and `b`, with `a` needing to precede `b`.
Based on the method signature, body, and constructors, 
we can write instances of `a`, `b` and `ignoringAnnotations` and required import statements  based on and the input specification:
  
Example 1:
    Part 1. The objects initialized:
        ```java
    
        Position temp1 = new Position(5, 10);
        Position temp2 = new Position(7, 6);
        Range temp3 = new Range(temp1, temp2);
        JavaToken temp4 = new JavaToken(temp3, 2, "token1", null, null);
        Position temp5 = new Position(8, 11);
        Position temp6 = new Position(10, 5);
        Range temp7 = new Range(temp5, temp6);
        JavaToken temp8 = new JavaToken(temp7, 4, "token2", null, null);
        TokenRange temp9 = new TokenRange(temp4, temp8);
        Node a = new UnknownType(temp9);
    
        Position temp10 = new Position(8, 5);
        Position temp11 = new Position(9, 10);
        Range temp12 = new Range(temp10, temp11);
        JavaToken temp13 = new JavaToken(temp12, 3, "token3", null, null);
        Position temp14 = new Position(10, 11);
        Position temp15 = new Position(11, 7);
        Range temp16 = new Range(temp14, temp15);
        JavaToken temp17 = new JavaToken(temp16, 1, "token4", null, null);
        TokenRange temp18 = new TokenRange(temp13, temp17);
        Node b = new UnknownType(temp18);
    
        boolean ignoringAnnotations = true;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```java
        import com.github.javaparser.ast.Node;
        import com.github.javaparser.ast.type.UnknownType;
        import com.github.javaparser.TokenRange;
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        ```
"""}
]

EXAMPLES_3_NON_STATIC = [
    {
        "code": """
TokenRange withBegin(JavaToken begin) {
    return new TokenRange(assertNotNull(begin), end);
}
    """, "constructors": """
Constructor of com.github.javaparser.JavaToken: JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken): {'previousToken': 'com.github.javaparser.JavaToken', 'kind': 'int', 'nextToken': 'com.github.javaparser.JavaToken', 'range': 'com.github.javaparser.Range', 'text': 'java.lang.String'}
Constructor of com.github.javaparser.Range: Range(Position begin, Position end): {'end': 'com.github.javaparser.Position', 'begin': 'com.github.javaparser.Position'}
Constructor of com.github.javaparser.Position: Position(int line, int column): {'line': 'int', 'column': 'int'}
    """, "cons": """
- class: com.github.javaparser.TokenRange
    - Constructors:
        - TokenRange(JavaToken begin, JavaToken end): {'begin': 'com.github.javaparser.JavaToken', 'end': 'com.github.javaparser.JavaToken'}
    """, "spec": """1. `begin`: is not null""",
        "answer": """
Based on the constructors I have understood before, we can instantiate the parameter `begin`.
According to the constructors, it is easy to instantiate a `begin`. 
`JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken)` can use to instantiate `begin`.
Then we can use "Range(Position begin, Position end)", "Position(int line, int column)" to instantiate hierarchically.
However this method is a non-static menthod in class `com.github.javaparser.TokenRange`, we should generate class object with the class constructors.
Based on the method signature, body, params constructors and class constructors, we can write test inputs of `begin` as Part.1, and class object `tokenRange` and its parameters as Part.2 and required import statements based on the input specification as Part.3:

Example 1:
    Part 1. Test inputs initialization statements:
        ```java
        Position temp1 = new Position(3, 7);
        Position temp2 = new Position(8, 4);
        Range temp3 = new Range(temp1, temp2);
        JavaToken begin = new JavaToken(temp3, 4, "begin", null, null);
        ```
        
    Part 2. Class object initialization statements:
        ```java
        JavaToken begin = new JavaToken(1);
        JavaToken end = new JavaToken(2);
        TokenRange tokenRange = new TokenRange(begin, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```java
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        import com.github.javaparser.TokenRange;
        ```

Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        Position temp1 = new Position(5, 2);
        Position temp2 = new Position(7, 9);
        Range temp3 = new Range(temp1, temp2);
        JavaToken begin = new JavaToken(temp3, 4, "begin", null, null);
        ```
        
    Part 2. Class object initialization statements:
        ```java
        JavaToken begin = new JavaToken(1, "begin");
        JavaToken end = new JavaToken(2, "end");
        TokenRange tokenRange = new TokenRange(begin, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```java
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        ```
"""}
]


class InputUnderstandingChain:
    def __init__(self, llm: ChatOpenAI) -> None:
        """
        Used to initialise LLMChain
        There are three chains:
            1. preliminary_shot_prompt: used to understand code and parameters
            2. further_shot_prompt: a hierarchical understanding of their subclasses for more complex parameters
            3. generator_shot_prompt： integrate the output of the previous times to generate test cases
        1. and 2. can specify a constructor which can be used to initialise parameter
        """
        self.llm = llm
        preliminary_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE_1),
            examples=EXAMPLES_1,
        )
        self.preliminary_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE_1),
                preliminary_shot_prompt,
            ] + QUESTION_MESSAGE_1
        )
        further_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE_2),
            examples=EXAMPLES_2,
        )
        self.further_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE_2),
                further_shot_prompt,
            ] + QUESTION_MESSAGE_2
        )
        generator_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE_3),
            examples=EXAMPLES_3,
        )
        self.generator_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE_3),
                generator_shot_prompt,
            ] + QUESTION_MESSAGE_3
        )
        generator_non_static_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE_3_NON_STATIC),
            examples=EXAMPLES_3_NON_STATIC,
        )
        self.generator_non_static_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE_3_NON_STATIC),
                generator_non_static_shot_prompt,
            ] + QUESTION_MESSAGE_3_NON_STATIC
        )
        # `types` is a set which record the type LLM has understood
        self.types = set()
        # `cons` is a string which includes the entire constructor generator_shot_prompt need to use
        self.cons = ""

    def parse_constructor(self, result: LLMResult):
        """
        Used to parse the result of preliminary_shot_prompt and further_prompt, which can specify a constructor
        """
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in
                re.finditer(r"- Constructor?:\n(.*?)(?=- Constructor?:\n|$)", text, re.M)]

    def parse_part1(self, result: LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"Part 1. .*?```java\n(.*?)```", text, re.M | re.S)]

    def parse_part3(self, result: LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"Part 3. .*?```java\n(.*?)```", text, re.M | re.S)]

    def parse_part2(self, result: LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"Part 2. .*?```java\n(.*?)```", text, re.M | re.S)]

    def init_dict(self, param_dict, param, layer, result) -> str:
        """
        Used to recursively extract a simpler dict from param_dict that contains
        only the constructor of the current class or a layer of its subclasses.
        :param param_dict: all parameters' info
        :param param: The parameter that needs to be resolved now
        :param result: a string contains info which has been resolved
        """
        p_info = param_dict.get(param)
        if p_info.get("__is_jdk_type__"):
            return result + f"  - {param}: a jdk-builtin type or cannot be parsed\n"
        else:
            class_type = p_info["classType"]
            result += f"  - {class_type}: {param}\n"
            if layer > 0:
                if p_info.get("constructors"):
                    result += "    - Constructors:\n"
                    for (signature, params) in p_info["constructors"].items():
                        result += f"        - {signature}: {params}\n"
                elif p_info.get("subClassName"):
                    result += "    - Sub classes name:\n"
                    flag = True
                    for name in p_info["subClassName"].values():
                        if param_dict.get(name).get("classType") == "class":
                            flag = False
                            result += f"        - {name}\n"
                    if flag:
                        for name in p_info["subClassName"].values():
                            result += f"        - {name}\n"
                        for name in p_info["subClassName"].values():
                            result = self.init_dict(param_dict, name, layer - 1, result)
                    else:
                        for name in p_info["subClassName"].values():
                            if param_dict.get(name).get("classType") == "class":
                                result = self.init_dict(param_dict, name, layer - 1, result)
                elif p_info.get("implementedClassName"):
                    result += "    - Implemented classes name:\n"
                    flag = True
                    for name in p_info["implementedClassName"].values():
                        if param_dict.get(name).get("classType") == "class":
                            flag = False
                            result += f"        - {name}\n"
                    if flag:
                        for name in p_info["implementedClassName"].values():
                            result += f"        - {name}\n"
                        for name in p_info["implementedClassName"].values():
                            result = self.init_dict(param_dict, name, layer - 1, result)
                    else:
                        for name in p_info["implementedClassName"].values():
                            if param_dict.get(name).get("classType") == "class":
                                result = self.init_dict(param_dict, name, layer - 1, result)
                elif p_info.get("subInterfaceName"):
                    result += "    - Implementation classes name:\n"
                    for name in p_info["subInterfaceName"].values():
                        result += f"        - {name}\n"
                    for name in p_info["subInterfaceName"].values():
                        result = self.init_dict(param_dict, name, layer - 1, result)
        return result

    def understand_further(self, constructor, param_dict: dict, spec):
        """
        Used to parse the parameters of a constructor
        :param constructor: current constructor to be resolved
        :param param_dict: all parameters' info
        :param spec: specification to be satisfied at parsing time
        """

        # c_param is a dict that holds information about the type of the parameter

        c_param = json.loads('{' + constructor.split('{').pop())

        result = ""
        for t in set(c_param.values()):
            if param_dict.get(t):
                result += self.init_dict(param_dict, t, 2, "")
        for n in c_param.keys():
            if c_param[n] in self.types:
                continue
            if param_dict.get(c_param[n]).get("__is_jdk_type__"):
                continue
            messages = self.further_prompt.format_messages(constructor=constructor, param=n,
                                                           deps=self.init_dict(param_dict, c_param[n], 2, ""),
                                                           spec=spec)
            for message in messages:
                print(f"\33[32m{message.content}\033[0m\n")
            llm_result: LLMResult = self.llm.generate([messages])
            self.types.add(c_param[n])
            cons_result = self.parse_constructor(llm_result).pop().replace("'", "\"")

            parse_type = c_param[n]
            # Putting the result of parsing into self.cons for subsequent use
            if param_dict.get(parse_type).get("classType") == 'abstract class' or \
                    param_dict.get(parse_type).get("classType") == 'interface':
                if param_dict.get(parse_type).get("subClassName") is not None:
                    self.cons = self.cons + "Sub class of " + parse_type + ": "
                    for sub_name in param_dict.get(parse_type).get("subClassName").values():
                        if param_dict.get(sub_name).get("constructors") is not None:
                            if constructor.split(":")[0] in param_dict.get(sub_name).get("constructors"):
                                self.cons += sub_name + "\nConstructor of " + sub_name + ": "
                                break
                if param_dict.get(parse_type).get("implementedClassName") is not None:
                    self.cons = self.cons + "Implemented class of " + parse_type + ": "
                    for sub_name in param_dict.get(parse_type).get("implementedClassName").values():
                        if param_dict.get(sub_name).get("constructors") is not None:
                            if constructor.split(":")[0] in param_dict.get(sub_name).get("constructors"):
                                self.cons += sub_name + "\nConstructor of " + sub_name + ": "
                                break
            self.cons += cons_result + "\n"

            # The parameters of the generated constructor need to be parsed again.
            self.understand_further(cons_result, param_dict, spec)

    def understand_param(self, code, spec, mg_dict: dict):
        """
        Used to understand the parameters of the method to be tested
        :param code: the code of method
        :param spec: specification to be satisfied at parsing time
        :param mg_dict: all parameters' info
        :return:
        """
        # Simplify all the type information and extract what is needed
        param_dict = util.mg_util.parameters(mg_dict, layer=10)

        if mg_dict.get("parameters"):
            p_type = mg_dict.get("parameters")
            for p in p_type.keys():
                if p_type.get(p) in self.types:
                    continue
                if param_dict.get(p_type.get(p)).get("__is_jdk_type__"):
                    continue
                self.types.add(p_type.get(p))
                messages = self.preliminary_prompt.format_messages(code=code,
                                                                   param=p,
                                                                   deps=self.init_dict(param_dict, p_type.get(p), 2,
                                                                                       ""),
                                                                   spec=spec)
                for message in messages:
                    print(f"\33[32m{message.content}\033[0m\n")
                llm_result: LLMResult = self.llm.generate([messages])
                constructor = self.parse_constructor(llm_result).pop().replace("'", "\"")

                parse_type = p_type.get(p)
                # Putting the result of parsing into self.cons for subsequent use
                if param_dict.get(parse_type).get("classType") == 'abstract class' or \
                        param_dict.get(parse_type).get("classType") == 'interface':
                    if param_dict.get(parse_type).get("subClassName") is not None:
                        self.cons = self.cons + "Sub class of " + parse_type + ": "
                        for sub_name in param_dict.get(parse_type).get("subClassName").values():
                            if param_dict.get(sub_name).get("constructors") is not None:
                                if constructor.split(":")[0] in param_dict.get(sub_name).get("constructors"):
                                    self.cons += sub_name + "\nConstructor of " + sub_name + ": "
                                    break
                    if param_dict.get(parse_type).get("implementedClassName") is not None:
                        self.cons = self.cons + "Implemented class of " + parse_type + ": "
                        for sub_name in param_dict.get(parse_type).get("implementedClassName").values():
                            if param_dict.get(sub_name).get("constructors") is not None:
                                if constructor.split(":")[0] in param_dict.get(sub_name).get("constructors"):
                                    self.cons += sub_name + "\nConstructor of " + sub_name + ": "
                                    break
                else:
                    self.cons = self.cons + "Constructor of " + p_type.get(p) + ": "
                self.cons += constructor + "\n"

                # The parameters of the generated constructor need to be parsed again.
                self.understand_further(constructor, param_dict, spec)

    def run(self, spec, mg_dict: dict):
        # Clear all cache information
        try:
            self.cons = ""
            self.types = set()
            self.understand_param(mg_dict["code"], spec, mg_dict)

            # Generate test cases
            if mg_dict["static"]:
                messages = self.generator_prompt.format_messages(code=mg_dict["code"], constructors=self.cons,
                                                                 spec=spec)
            else:
                class_name = mg_dict["className"]
                constructor = mg_dict["nodes"][class_name]["constructors"]
                builders = mg_dict["nodes"][class_name]["builders"]
                constructor_str = "- class: " + class_name + "\n"
                if len(constructor) != 0:
                    constructor_str += "\t- Constructors: \n"
                    for k in constructor.keys():
                        constructor_str += "\t\t- " + k + ": " + str(constructor[k]) + "\n"
                if len(builders) != 0:
                    constructor_str += "\t- Builders: \n"
                    for k in builders.keys():
                        constructor_str += "\t\t- " + k + ": " + str(builders[k]) + "\n"
                messages = self.generator_non_static_prompt.format_messages(code=mg_dict["code"],
                                                                            constructors=self.cons,
                                                                            cons=constructor_str, spec=spec)
            for message in messages:
                print(f"\33[32m{message.content}\033[0m\n")
            llm_result: LLMResult = self.llm.generate([messages])
            if mg_dict["static"]:
                return {
                    "java": self.parse_part1(llm_result),
                    "cons": [],
                    "import": self.parse_part2(llm_result)
                }
            else:
                return {
                    "java": self.parse_part1(llm_result),
                    "cons": self.parse_part2(llm_result),
                    "import": self.parse_part3(llm_result)
                }
        except:
            return {
                "java": "",
                "cons": "",
                "import": ""
            }


if __name__ == "__main__":
    from config import *

    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0)
    chain = InputUnderstandingChain(llm)
    code = """boolean areInOrder(Node a, Node b){
    return areInOrder(a, b, false);
}"""
    file = open("../../../graph.json", "r")
    file_content = file.read()
    file.close()
    mg1 = json.loads(file_content.replace("\n", ""))
    param_dict = util.mg_util.parameters(mg1, layer=3)
    print(param_dict)
