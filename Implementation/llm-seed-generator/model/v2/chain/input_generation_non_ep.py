import re

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.schema import LLMResult


SYSTEM_MESSAGE = """
You are an experienced tester. Now you are expected to write test inputs for the provided API method.
Your answer must contain two part, Part.1 is the code to instantiate the objects and Part.2 is the required import statements.
"""

QUESTION_MESSAGE = [
    ("human",
     "API Method: ```java {code}```\n\n\n"),
    ("ai", "Answer: Let's do this step by step. "),
]

EXAMPLE_MESSAGE = [
    ("human",
     "API Method: ```java {code}```\n\n\n"),
    ("ai", "Answer: Let's do this step by step. {answer}"),
]

SYSTEM_MESSAGE_NON_STATIC = """
You are an experienced tester. Now you are expected to write test inputs for the provided API method.
This method is a non-static method, so you also need to write the initialisation statement for the class object to achieve high coverage based on the Class Constructors.
Your answer is able to contains a lot of examples. Every example must contains three parts. 
Part.1 contains test inputs initialization statements. Part.2 contains complete class object initialization statements with all parameters. Part.3 is the required import statements.
"""

QUESTION_MESSAGE_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nClass Constructors: {cons}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nClass Constructors: {cons}\n\n\n"),
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
        ```import
        import java.lang.String;
        ```

Example 2:
    Part 1. The objects initialized:
        ```java
        String str = "";
        char ch = 's';
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        ```
        
Example 3:
    Part 1. The objects initialized:
        ```java
        String str = "sdhfuojds";
        char ch = 'd';
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        ```
    
Example 4:
    Part 1. The objects initialized:
        ```java
        String str = "fgvweatkyu";
        char ch = 'p';
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        ```
    """}, {
        "code": """
    <E> List<E> union(final List<? extends E> list1, final List<? extends E> list2) {
        final ArrayList<E> result = new ArrayList<>(list1.size() + list2.size());
        result.addAll(list1);
        result.addAll(list2);
        return result;
    }
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `list1` and `list2`.
According to the code, we can know that the method is used to union `list1` and `list2`.
Based on the method signature, body, we can write instances of `list1` and `list2` and required import statements to achieve high coverage:

Example 1: 
    Part 1. The objects initialized:
        ```java
        List<String> list1 = new ArrayList<>();
        List<String> list2 = new LinkedList<>();
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.util.List;
        import java.util.ArrayList;
        import java.util.LinkedList;
        ```

Example 2:
    Part 1. The objects initialized:
        ```java
        List<Integer> list1 = new ArrayList<>();
        List<Integer> list2 = new LinkedList<>();
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        import java.util.List;
        import java.util.ArrayList;
        import java.util.LinkedList;
        ```
        
Example 3:
    Part 1. The objects initialized:
        ```java
        List<Integer> list1 = null;
        List<Integer> list2 = new LinkedList<>();
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        import java.util.List;
        import java.util.ArrayList;
        import java.util.LinkedList;
        ```
        
Example 4:
    Part 1. The objects initialized:
        ```java
        List<Integer> list1 = new ArrayList<>();
        List<Integer> list2 = null;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        import java.util.List;
        import java.util.ArrayList;
        import java.util.LinkedList;
        ```
    """}, {
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
        ```import
        import java.lang.Integer;
        ```

Example 2:
    Part 1. The objects initialized:
        ```java
        int startInclusive = 3;
        int endExclusive = 3;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        ```
        
Example 3:
    Part 1. The objects initialized:
        ```java
        int startInclusive = 3;
        int endExclusive = 2;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        ```
    """}, {
        "code": """
    void bubbleSort(int[] array) {
        for (int i = 0; i < arr.length - 1; i++) {
            for (int j = 0; j < arr.length - i - 1; j++) {
                if (array[j] > array[j + 1]){
                    int temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                }
            }
        }
    }
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `array`.
According to the code, we can know that the method is used to make `array` orderly.
Based on the method signature, body, and dependent types, we can write instances of `array` and required import statements to achieve high coverage:

Example 1: 
    Part 1. The objects initialized:
        ```java
        int[] array = null;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        ```

Example 2:
    Part 1. The objects initialized:
        ```java
        int[] array = {2, 6, 3, 1, 8};
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        ```
        
Example 3:
    Part 1. The objects initialized:
        ```java
        int[] array = {5, 5, 5};
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Integer;
        ```
    """}
]

EXAMPLES_NON_STATIC = [
    {
        "code": """
    void setValue(final Number value) {
        this.value = value.byteValue();
    }
    """, "cons": """
- class: org.apache.commons.lang3.mutable.MutableByte
    - Constructors:
        - MutableByte(): {}
        - MutableByte(final byte value): {'value': 'byte'}
        - MutableByte(final Number value): {'value': 'java.lang.Number'}
        - MutableByte(final String value): {'value': 'java.lang.String'}
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `value`.
However, method use the field `value` which was in class. We should generate the object with different value of the class to achieve high coverage.
Based on the method signature, body, we can write test inputs of `operand` as Part.1, class object `mutableByte` and its parameters as Part.2 and required import statements as Part.3:

Example 1: 
    Part 1. Test inputs initialization statements:
        ```java
        Number value = null;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        byte value = 2;
        MutableByte mutableByte = new MutableByte(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Number;
        import java.lang.Byte;
        import org.apache.commons.lang3.mutable.MutableDouble;
        ```

Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        Number value = new Byte((byte) 2);
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        String value = "2";
        MutableByte mutableByte = new MutableByte(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Number;
        import java.lang.Byte;
        import java.lang.String;
        import org.apache.commons.lang3.mutable.MutableDouble;
        ```
        
Example 3:
    Part 1. Test inputs initialization statements:
        ```java
        Number value = 3;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        String value = "2";
        MutableByte mutableByte = new MutableByte(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Number;
        import java.lang.String;
        import org.apache.commons.lang3.mutable.MutableDouble;
        ```
    """}, {
        "code": """
    double addAndGet(final double operand) {
        this.value += operand;
        return value;
    }
    """, "cons": """
- class: org.apache.commons.lang3.mutable.MutableDouble
    - Constructors:
        - MutableDouble(): {}
        - MutableDouble(final double value): {'value': 'double'}
        - MutableDouble(final Number value): {'value': 'java.lang.Number'}
        - MutableDouble(final String value): {'value': 'java.lang.String'}
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `operand`.
However, method use the field `value` which was in class. We should generate the object with different value of the class to achieve high coverage.
Based on the method signature, body, we can write test inputs of `operand` as Part.1, class object `mutableDouble` and its parameters as Part.2 and required import statements as Part.3:

Example 1: 
    Part 1. Test inputs initialization statements:
        ```java
        double operand = 1.2;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        double value = 2.5;
        MutableDouble mutableDouble = new MutableDouble(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Double;
        import org.apache.commons.lang3.mutable.MutableDouble;
        ```

Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        double operand = -4.3;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        String value = "1.4";
        MutableDouble mutableDouble = new MutableDouble(value);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Double;
        import org.apache.commons.lang3.mutable.MutableDouble;
        import java.lang.String;
    ```
"""}, {
        "code": """
    boolean contains(final char ch) {
        return (ch >= start && ch <= end) != negated;
    }
    """, "cons": """
- class: org.apache.commons.lang3.CharRange
    - Builders:
        - is(final char ch): {'ch': 'char'}
        - isNot(final char ch): {'ch': 'char'}
        - isIn(final char start, final char end): {'start': 'char', 'end': 'char'}
        - isNotIn(final char start, final char end): {'start': 'char', 'end': 'char'}
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `ch`.
However, method use the field `start` and `end` which are in class. According to the code, we can know that class object `charRange` should has a range.
So we can generate the object with different value of the class to achieve high coverage via the builders `isIn(final char start, final char end)`.
Based on the method signature, body, we can write test inputs of `ch` as Part.1, class object `charRange` and its parameters as Part.2 and required import statements as Part.3:

Example 1: 
    Part 1. Test inputs initialization statements:
        ```java
        char ch = 't';
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        char start = 'q';
        char end = 'w';
        CharRange charRange = CharRange.isIn(start, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Character;
        import org.apache.commons.lang3.CharRange;
        ```

Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        char ch = 'm';
        ```
    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        char start = 'a';
        char end = 'h';
        CharRange charRange = CharRange.isIn(start, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.Character;
        import org.apache.commons.lang3.CharRange;
        ```
    """}, {
        "code": """
    String replace(final String source, final int offset, final int length) {
        if (source == null) {
            return null;
        }
        final StrBuilder buf = new StrBuilder(length).append(source, offset, length);
        if (!substitute(buf, 0, length)) {
            return source.substring(offset, offset + length);
        }
        return buf.toString();
    }
    """, "cons": """
- class: org.apache.commons.lang3.text.StrSubstitutor
    - Builders:
        - StrSubstitutor(): {}
        - StrSubstitutor(final Map<String, V> valueMap): {'valueMap': 'java.util.Map'}
        - StrSubstitutor(final Map<String, V> valueMap, final String prefix, final String suffix): {'valueMap': 'java.util.Map', 'prefix': 'java.lang.String', 'suffix': 'java.lang.String'}
        - StrSubstitutor(final Map<String, V> valueMap, final String prefix, final String suffix, final char escape): {'valueMap': 'java.util.Map', 'prefix': 'java.lang.String', 'suffix': 'java.lang.String', 'escape': 'char'}

    """, "answer": """
According to the signature of the code, we can know that we should write instances of `source`, `offset`, `length`.
However, `substitute` is a method in class `org.apache.commons.lang3.text.StrSubstitutor`, we should generate the object with different value of the class to achieve high coverage.
Based on the method signature, body, we can write test inputs of `source`, `offset`, `length` as Part.1, class object `strSubstitutor` and its parameters as Part.2 and required import statements as Part.3:

Example 1: 
    Part 1. Test inputs initialization statements:
        ```java
        String source = "aklfshdjlhf";
        int offset = 3;
        int length = 5;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        HashMap<String, String> valueMap = new HashMap<>();
        valueMap.add("abc", "def");
        valueMap.add("zyx", "wvu");
        StrSubstitutor strSubstitutor = new StrSubstitutor(valueMap);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.lang.Integer;
        import java.util.HashMap;
        import org.apache.commons.lang3.text.StrSubstitutor;
        ```

Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        String source = "fgxhj";
        int offset = 1;
        int length = 4;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        HashMap<String, Integer> valueMap = new HashMap<>();
        valueMap.add("fghj", 2);
        valueMap.add("sdfgg", 1);
        valueMap.add("jk", 3);
        StrSubstitutor strSubstitutor = new StrSubstitutor(valueMap, "*", "?");
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.lang.Integer;
        import java.util.HashMap;
        import org.apache.commons.lang3.text.StrSubstitutor;
        ```
        
Example 2:
    Part 1. Test inputs initialization statements:
        ```java
        String source = "lioklg";
        int offset = 5;
        int length = 3;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        HashMap<String, Integer> valueMap = new HashMap<>();
        valueMap.add("lioklg", 1);
        valueMap.add("fsdg", 2);
        valueMap.add("oipy7i", 3);
        StrSubstitutor strSubstitutor = new StrSubstitutor(valueMap, "/", ".");
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.lang.Integer;
        import java.util.HashMap;
        import org.apache.commons.lang3.text.StrSubstitutor;
        ```
    """}, {
        "code": """
    public DiffBuilder<T> append(final String fieldName, final char[] lhs,
            final char[] rhs) {
        validateFieldNameNotNull(fieldName);

        if (objectsTriviallyEqual) {
            return this;
        }
        if (!Arrays.equals(lhs, rhs)) {
            diffs.add(new Diff<Character[]>(fieldName) {
                private static final long serialVersionUID = 1L;

                @Override
                public Character[] getLeft() {
                    return ArrayUtils.toObject(lhs);
                }

                @Override
                public Character[] getRight() {
                    return ArrayUtils.toObject(rhs);
                }
            });
        }
        return this;
    }
    """, "cons": """
- class: org.apache.commons.lang3.builder.DiffBuilder
    - Constructors: 
        - DiffBuilder(final T lhs, final T rhs, final ToStringStyle style, final boolean testTriviallyEqual): {'testTriviallyEqual': 'boolean', 'lhs': 'T', 'style': 'org.apache.commons.lang3.builder.ToStringStyle', 'rhs': 'T'}
        - DiffBuilder(final T lhs, final T rhs, final ToStringStyle style): {'lhs': 'T', 'style': 'org.apache.commons.lang3.builder.ToStringStyle', 'rhs': 'T'}
    """, "answer": """
According to the signature of the code, we can know that we should write instances of `fieldName`, `lhs`, `rhs`.
However, this method is a non-static method, we should generate the object with different value of the class to achieve high coverage.
Based on the method signature, body, we can write test inputs of `fieldName`, `lhs`, `rhs` as Part.1, class object `diffBuilder` and its parameters as Part.2 and required import statements as Part.3:

Example 1: 
    Part 1. Test inputs initialization statements:
        ```java
        String fieldName = "array";
        char[] lhs = null;
        char[] rhs = {'1', '2', '3'};
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        Character[] lhs = {'1', '2', '3'};
        Character[] rhs = {'4', '5', '6'};
        ToStringStyle style = ToStringStyle.JSON_STYLE;
        DiffBuilder<Character[]> diffBuilder = new DiffBuilder<>(lhs, rhs, style);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.lang.Character;
        import org.apache.commons.lang3.builder.DiffBuilder;
        import org.apache.commons.lang3.builder.ToStringStyle;
        ```

Example 2: 
    Part 1. Test inputs initialization statements:
        ```java
        String fieldName = "array";
        char[] lhs = {'a', 'b', 'c'};
        char[] rhs = null;
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        Character[] lhs = {'a', 'b', 'c'};
        Character[] rhs = {'d', 'e', 'f'};
        ToStringStyle style = ToStringStyle.JSON_STYLE;
        boolean testTriviallyEqual = false;
        DiffBuilder<Character[]> diffBuilder = new DiffBuilder<>(lhs, rhs, style, testTriviallyEqual);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.lang.Character;
        import java.lang.Boolean;
        import org.apache.commons.lang3.builder.DiffBuilder;
        import org.apache.commons.lang3.builder.ToStringStyle;
        ```
        
Example 3: 
    Part 1. Test inputs initialization statements:
        ```java
        String fieldName = "array";
        char[] lhs = {'a', 'b', 'c'};
        char[] rhs = {'d', 'e', 'f'};
        ```

    Part 2. Class object and constructor arguments initialization statements:
        ```class object
        Character[] lhs = {'a', 'b', 'c'};
        Character[] rhs = {'d', 'e', 'f'};
        ToStringStyle style = ToStringStyle.JSON_STYLE;
        boolean testTriviallyEqual = false;
        DiffBuilder<Character[]> diffBuilder = new DiffBuilder<>(lhs, rhs, style, testTriviallyEqual);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import java.lang.String;
        import java.lang.Character;
        import java.lang.Boolean;
        import org.apache.commons.lang3.builder.DiffBuilder;
        import org.apache.commons.lang3.builder.ToStringStyle;
        ```
    """}
]
           
class InputGenerationNonEPChain:
    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE),
            examples=EXAMPLES,
            # examples=[]
        )
        self.final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE),
                few_shot_prompt,
            ] + QUESTION_MESSAGE
        )

        few_shot_prompt_non_static = FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages(EXAMPLE_MESSAGE_NON_STATIC),
            examples=EXAMPLES_NON_STATIC,
            # examples=[]
        )
        self.final_prompt_non_static = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_MESSAGE_NON_STATIC),
                few_shot_prompt_non_static,
            ] + QUESTION_MESSAGE_NON_STATIC
        )

    def parse_java(self, result: LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"```java\n(.*?)```", text, re.M|re.S)]

    def parse_cons(self, result:LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"```class object\n(.*?)```", text, re.M|re.S)]

    def parse_import(self, result:LLMResult):
        text = result.generations[0][0].text
        print(text)
        return [mobj.group(1).strip() for mobj in re.finditer(r"```import\n(.*?)```", text, re.M|re.S)]

        
    def run(self, mg_dict: dict):
        if mg_dict["static"]:
            messages = self.final_prompt.format_messages(code=mg_dict["code"])
        else:
            class_name = mg_dict["className"]
            constructor = mg_dict["nodes"][class_name].get("constructors")
            builders = mg_dict["nodes"][class_name].get("builders")
            constructor_str = "- class: " + class_name + "\n"
            if constructor is not None:
                constructor_str += "\t- Constructors: \n"
                for k in constructor.keys():
                    constructor_str += "\t\t- " + k + ": " + str(constructor[k]) + "\n"
            if builders is not None:
                constructor_str += "\t- Builders: \n"
                for k in builders.keys():
                    constructor_str += "\t\t- " + k + ": " + str(builders[k]) + "\n"

            messages = self.final_prompt_non_static.format_messages(code=mg_dict["code"], cons=constructor_str)
        for message in messages:
            print(f"\33[32m{message.content}\033[0m\n")
        llm_result: LLMResult = self.llm.generate([messages])
        return {
            "java": self.parse_java(llm_result),
            "cons": self.parse_cons(llm_result),
            "import": self.parse_import(llm_result)
        }





if __name__ == "__main__":
    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0)
    chain = InputGenerationNonEPChain(llm)