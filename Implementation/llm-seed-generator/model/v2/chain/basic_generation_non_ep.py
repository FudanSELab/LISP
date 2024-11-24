import json
import re
import logging

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.chains import LLMChain
from langchain.schema import LLMResult
import util.mg_util

SYSTEM_MESSAGE = """
You are an experienced tester. Now you are expected to write test inputs for the provided API method.
Your answer must contain two part, Part.1 is the code to instantiate the objects and Part.2 is the required import statements.
"""

QUESTION_MESSAGE = [
    ("human",
     "API Method: ```java {code}```\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE = [
    ("human",
     "API Method: ```java {code}```\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

SYSTEM_MESSAGE_NON_STATIC = """
You are an experienced tester. Now you are expected to write test inputs for the provided API method.
This method is a non-static method, so you also need to write the initialisation statement for the class object to achieve high coverage.
Your answer is able to contains a lot of examples. Every example must contains three parts. 
Part.1 contains test inputs initialization statements. Part.2 contains complete class object initialization statements with all parameters. Part.3 is the required import statements.
"""

QUESTION_MESSAGE_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nClass Name: {name}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nClass Name: {name}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

EXAMPLES = [
    {
        "code": """
        int countMatches(final CharSequence str, final char ch) {
            if (isEmpty(str)) {
                return 0;
            }
            int count = 0;
            for (int i = 0; i < str.length(); i++) {
                if (ch == str.charAt(i)) {
                    count++;
                }
            }
            return count;
        }
        """, "answer": """
According to the signature of the code, we can know that we should write instances of `str` and `sh`.
According to the code, we can know that the method is used to search `ch` in `str`.
Based on the method signature, body, we can write instances of `str` and `ch` and required import statements to achieve high coverage:

Example 1: 
    Part 1. The objects initialized:
        ```java
        String str = null;
        char ch = 'j';
        ```

        Part 2. According to the code above, the following import statement must be required:
            ```java
            import java.lang.String;
            ```

    Example 2:
        Part 1. The objects initialized:
            ```java
            String str = "";
            char ch = 's';
            ```

        Part 2. According to the code above, the following import statement must be required:
            ```java
            import java.lang.String;
            ```

    Example 3:
        Part 1. The objects initialized:
            ```java
            String str = "sdhfuojds";
            char ch = 'd';
            ```

        Part 2. According to the code above, the following import statement must be required:
            ```java
            import java.lang.String;
            ```

    Example 4:
        Part 1. The objects initialized:
            ```java
            String str = "fgvweatkyu";
            char ch = 'p';
            ```

        Part 2. According to the code above, the following import statement must be required:
            ```java
            import java.lang.String;
            ```
"""},{
        "code": """
    int nextInt(final int startInclusive, final int endExclusive) {
        Validate.isTrue(endExclusive >= startInclusive,
                "Start value must be smaller or equal to end value.");
        Validate.isTrue(startInclusive >= 0, "Both range values must be non-negative.");

        if (startInclusive == endExclusive) {
            return startInclusive;
        }

        return startInclusive + random().nextInt(endExclusive - startInclusive);
    }
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `startInclusive` and `endExclusive`.
According to the code, we can know that the method is used to generate a random integer from `startInclusive` to `endExclusive`.
Based on the method signature, body, and dependent types, we can write instances of `startInclusive` and `endExclusive` and required import statements to achieve high coverage:

Example 1: 
    Part 1. The objects initialized:
        ```java
        int startInclusive = 2;
        int endExclusive = 3;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```java
        import java.lang.Integer;
        ```

Example 2:
    Part 1. The objects initialized:
        ```java
        int startInclusive = 3;
        int endExclusive = 3;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```java
        import java.lang.Integer;
        ```

Example 3:
    Part 1. The objects initialized:
        ```java
        int startInclusive = 3;
        int endExclusive = 2;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```java
        import java.lang.Integer;
        ```
    """
    }, {
        "code": """
boolean areInOrder(Node a, Node b, boolean ignoringAnnotations) {
    return compare(a, b, ignoringAnnotations) <= 0;
}
""", "answer": """
Based on the signature of the method, we can instantiate the parameter `a`, `b` and `ignoringAnnotations`.
`a` and `b`'s type is `Node`, and the code of the method use the method `compare`.
So we can infer that `Node` is `com.github.javaparser.ast.Node`.
Based on the method signature, body, and code, 
we can write instances of `a`, `b` and `ignoringAnnotations` and required import statements to achieve high coverage:

Example 1:
    Part 1. The objects initialized:
        ```java

        Node a = null;
        Node b = null;
        boolean ignoringAnnotations = true;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```java
        import com.github.javaparser.ast.Node;
        ```

Example 2:
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

Example 3:
    Part 1. The objects initialized:
        ```java

        Position temp1 = new Position(9, 3);
        Position temp2 = new Position(10, 6);
        Range temp3 = new Range(temp1, temp2);
        JavaToken temp4 = new JavaToken(temp3, 2, "token1", null, null);
        Position temp5 = new Position(12, 4);
        Position temp6 = new Position(14, 10);
        Range temp7 = new Range(temp5, temp6);
        JavaToken temp8 = new JavaToken(temp7, 4, "token2", null, null);
        TokenRange temp9 = new TokenRange(temp4, temp8);
        Node a = new UnknownType(temp9);

        Position temp10 = new Position(5, 6);
        Position temp11 = new Position(6, 8);
        Range temp12 = new Range(temp10, temp11);
        JavaToken temp13 = new JavaToken(temp12, 3, "token3", null, null);
        Position temp14 = new Position(7, 11);
        Position temp15 = new Position(8, 9);
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
"""
    }
]

EXAMPLES_NON_STATIC = [
    {
"code": """
    double addAndGet(final double operand) {
        this.value += operand;
        return value;
    }
    """, "name": """org.apache.commons.lang3.mutable.MutableDouble""",
        "answer": """
According to the signature of the code, we can know that we should write instances of `operand`.
However, method use the field `value` which was in class. We should generate the object with different value of the class to achieve high coverage.
Based on the method signature, body, we can write test inputs of `operand` as Part.1, class object `mutableDouble` and its parameters as Part.2 and required import statements as Part.3:

Example 1: 
    Part 1. Test inputs initialization statements:
        ```java
        double operand = 1.2;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```java
        double value = 2.5;
        MutableDouble mutableDouble = new MutableDouble(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```java
        import java.lang.Double;
        import org.apache.commons.lang3.mutable.MutableDouble;
        ```

Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        double operand = -4.3;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```java
        String value = "1.4";
        MutableDouble mutableDouble = new MutableDouble(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```java
        import java.lang.Double;
        import org.apache.commons.lang3.mutable.MutableDouble;
        import java.lang.String;
    ```
"""}, {
        "code": """
TokenRange withBegin(JavaToken begin) {
    return new TokenRange(assertNotNull(begin), end);
}
""", "name": """com.github.javaparser.TokenRange"""
    , "answer": """
Based on the signature of the method, we should instantiate the parameter `begin`.
`begin`'s type is `JavaToken`, and the code of the method use the type `TokenRange`.
So we can infer that the `JavaToken` is `com.github.javaparser.JavaToken`.
Method use the field `end`, so we should instantiate the class `TokenRange`.
Based on the method signature, type inference, and code, 
we can write instances of `begin` and required import statements to achieve high coverage:

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
        Position temp1 = null;
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
        
Example 3:
    Part 1. Test inputs initialization statements:
        ```java
        Position temp1 = new Position(3, 7);
        Position temp2 = null;
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

class BasicGenerationNonEP:
    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        generator_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE),
            examples=EXAMPLES,
        )
        self.generator_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE),
                generator_shot_prompt,
            ] + QUESTION_MESSAGE
        )
        generator_non_static_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE_NON_STATIC),
            examples=EXAMPLES_NON_STATIC,
        )
        self.generator_non_static_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE_NON_STATIC),
                generator_non_static_shot_prompt,
            ] + QUESTION_MESSAGE_NON_STATIC
        )

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

    def run(self, mg_dict: dict):
        class_name = mg_dict["className"]
        # Generate test cases
        if mg_dict["static"]:
            messages = self.generator_prompt.format_messages(code=mg_dict["code"])
        else:
            messages = self.generator_non_static_prompt.format_messages(code=mg_dict["code"], name=class_name)
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


if __name__ == "__main__":
    from config import *

    str = """
Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        char negativeSign = '#';
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```java
        char zeroDigit = '0';
        char positiveSign = '+';
        char negativeSign = '#';
        char decimalSeparator = '.';
        DecimalStyle decimalStyle = new DecimalStyle(zeroDigit, positiveSign, negativeSign, decimalSeparator);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```java
        import org.threeten.bp.format.DecimalStyle;
        ```
"""
    print([mobj.group(1).strip() for mobj in re.finditer(r"Part 2. .*?```java\n(.*?)```", str, re.M | re.S)])
