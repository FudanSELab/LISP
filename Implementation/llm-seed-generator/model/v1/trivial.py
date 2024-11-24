import json

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from util.mg_util import parameter_info

SYSTEM_MESSAGE_CONTENT = """
You are an experienced test engineer.
Now you are expected to write test cases based on the given requirements and the information of API method.
"""

FEW_SHOT_EXAMPLES = [
    {
        "question": """
* Method Signature: TimeZone getGmtTimeZone(final String pattern)
* Type Information:
    - String: jdk built-in type
* Method Body: ```java
public static TimeZone getGmtTimeZone(final String pattern) {
    if ("Z".equals(pattern) || "UTC".equals(pattern)) {
        return GREENWICH;
    }

    final Matcher m = GMT_PATTERN.matcher(pattern);
    if (m.matches()) {
        final int hours = parseInt(m.group(2));
        final int minutes = parseInt(m.group(4));
        if (hours == 0 && minutes == 0) {
            return GREENWICH;
        }
        return new GmtTimeZone(parseSign(m.group(1)), hours, minutes);
    }
    return null;
}
```
""",
        "answer": """
Based on the name of method and parameters, this method retrieves a time zone based on the given pattern.
Based on the type of parameters, the pattern is related to the time zone.
Based on the body of method, when pattern equals "Z" or "UTC", it can achieve higher coverage.
Therefore, we can derive the following test case:
```java
public void testGetGmtTimeZone() {
    // Test cases for getGmtTimeZone method

    // Test with valid pattern "Z"
    TimeZone timeZone1 = TimeZone.getGmtTimeZone("Z");
    assertEquals(TimeZone.GREENWICH, timeZone1);

    // Test with valid pattern "UTC"
    TimeZone timeZone2 = TimeZone.getGmtTimeZone("UTC");
    assertEquals(TimeZone.GREENWICH, timeZone2);

    // Test with valid pattern "+01:30"
    TimeZone timeZone3 = TimeZone.getGmtTimeZone("+01:30");
    assertEquals(1, timeZone3.getSign());
    assertEquals(1, timeZone3.getHours());
    assertEquals(30, timeZone3.getMinutes());

    // Test with valid pattern "-08:00"
    TimeZone timeZone4 = TimeZone.getGmtTimeZone("-08:00");
    assertEquals(-1, timeZone4.getSign());
    assertEquals(8, timeZone4.getHours());
    assertEquals(0, timeZone4.getMinutes());

    // Test with invalid pattern
    TimeZone timeZone5 = TimeZone.getGmtTimeZone("invalid");
    assertNull(timeZone5);
}
```
"""
    }
]

FINAL_QUESTION_PROMPT_TEMPLATE = """
* Method Signature: {method_signature}
* Type Information: {type_information}
* Method Body: {method_body}
"""


class V1TrivialChatter:
    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.system_msg = SystemMessage(content=SYSTEM_MESSAGE_CONTENT)
        self.few_shot_msgs = []
        for eg in FEW_SHOT_EXAMPLES:
            self.few_shot_msgs.append(HumanMessage(content=eg["question"]))
            self.few_shot_msgs.append(AIMessage(content=eg["answer"]))

    def format_template(self, mg, method_signature: str) -> str:
        final_question_msg = HumanMessage(content=FINAL_QUESTION_PROMPT_TEMPLATE.format(
            method_signature=method_signature,
            type_information=parameter_info(mg, layer=5),
            method_body=mg["code"]
        ))
        final_prompt_tmpl = ChatPromptTemplate.from_messages([
            self.system_msg,
            *self.few_shot_msgs,
            final_question_msg
        ])
        return final_prompt_tmpl.format()

    def chat(self, mg, method_signature: str):
        formatted_prompt = self.format_template(mg, method_signature)
        return self.llm.predict(formatted_prompt)


if __name__ == "__main__":
    test_data1 = '''{"returnTypeName":"boolean","methodName":"areInOrder","parameters":{"a":"com.github.javaparser.ast.Node","b":"com.github.javaparser.ast.Node"},"code":"{\n    return areInOrder(a, b, false);\n}","nodes":{"com.github.javaparser.Range":{"superClassName":"java.lang.Object","interfaces":[],"fields":{},"constructors":{"Range(Position, Position)":{"end":"com.github.javaparser.Position","begin":"com.github.javaparser.Position"}}},"java.lang.Cloneable":{},"com.github.javaparser.JavaToken":{"superClassName":"java.lang.Object","interfaces":[],"fields":{},"constructors":{"Kind(int)":{"kind":"int"},"JavaToken(Token, List)":{"tokens":"java.util.List","token":"com.github.javaparser.Token"},"JavaToken(Range, int, String, JavaToken, JavaToken)":{"previousToken":"com.github.javaparser.JavaToken","kind":"int","nextToken":"com.github.javaparser.JavaToken","range":"com.github.javaparser.Range","text":"java.lang.String"},"JavaToken(int)":{"kind":"int"},"JavaToken()":{},"JavaToken(int, String)":{"kind":"int","text":"java.lang.String"}}},"com.github.javaparser.Position":{"superClassName":"java.lang.Object","interfaces":["java.lang.Comparable"],"fields":{},"constructors":{"Position(int, int)":{"line":"int","column":"int"}}},"java.lang.Iterable":{},"int":{},"java.io.Serializable":{},"com.github.javaparser.ast.visitor.Visitable":{},"java.util.List":{},"com.github.javaparser.TokenBase":{"superClassName":"java.lang.Object","interfaces":[],"fields":{},"constructors":{}},"com.github.javaparser.ast.nodeTypes.NodeWithTokenRange":{},"com.github.javaparser.Token":{"superClassName":"com.github.javaparser.TokenBase","interfaces":["java.io.Serializable"],"fields":{},"constructors":{"Token(int, String)":{"nKind":"int","sImage":"java.lang.String"},"Token()":{},"Token(int)":{"nKind":"int"}}},"java.lang.Object":{},"java.lang.Comparable":{},"java.lang.String":{},"com.github.javaparser.HasParentNode":{},"com.github.javaparser.ast.Node":{"superClassName":"java.lang.Object","interfaces":["java.lang.Cloneable","com.github.javaparser.ast.visitor.Visitable","com.github.javaparser.ast.nodeTypes.NodeWithTokenRange","com.github.javaparser.HasParentNode","com.github.javaparser.ast.nodeTypes.NodeWithRange"],"fields":{},"constructors":{"DirectChildrenIterator(Node)":{"node":"com.github.javaparser.ast.Node"},"PostOrderIterator(Node)":{"root":"com.github.javaparser.ast.Node"},"ParentsVisitor(Node)":{"node":"com.github.javaparser.ast.Node"},"PreOrderIterator(Node)":{"node":"com.github.javaparser.ast.Node"},"Node(TokenRange)":{"tokenRange":"com.github.javaparser.TokenRange"},"BreadthFirstIterator(Node)":{"node":"com.github.javaparser.ast.Node"}}},"com.github.javaparser.ast.nodeTypes.NodeWithRange":{},"com.github.javaparser.TokenRange":{"superClassName":"java.lang.Object","interfaces":["java.lang.Iterable"],"fields":{},"constructors":{"TokenRange(JavaToken, JavaToken)":{"end":"com.github.javaparser.JavaToken","begin":"com.github.javaparser.JavaToken"}}}}}'''
    mg1 = json.loads(test_data1.replace("\n", ""))

    llm = ChatOpenAI(openai_api_key="api-key")
    chatter = V1TrivialChatter(llm)
    prompt = chatter.format_template(mg1, "com.github.javaparser.utils.PositionUtils::areInOrder(Node a, Node b)")
    print(prompt)

    result = chatter.chat(mg1, "com.github.javaparser.utils.PositionUtils::areInOrder(Node a, Node b)")
    print(result)
