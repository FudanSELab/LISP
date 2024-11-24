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
     "API Method: ```java {code}```\n\nInput Specification: {spec}\n\nDependent Types: {deps}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE = [
    ("human",
     "API Method: ```java {code}```\n\nInput Specification: {spec}\n\nDependent Types: {deps}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

SYSTEM_MESSAGE_NON_STATIC = """
You are an experienced tester. Now you are expected to write test inputs for the provided API method.
This method is a non-static method, so you also need to write the initialisation statement for the class object to achieve high coverage based on the Class Constructors.
Your answer is able to contains a lot of examples. Every example must contains three parts. 
Part.1 contains test inputs initialization statements. Part.2 contains complete class object initialization statements with all parameters. Part.3 is the required import statements.
"""

QUESTION_MESSAGE_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nInput Specification: {spec}\n\nDependent Types: {deps}\n\nClass Constructor: {cons}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. "),
]

EXAMPLE_MESSAGE_NON_STATIC = [
    ("human",
     "API Method: ```java {code}```\n\nInput Specification: {spec}\n\nDependent Types: {deps}\n\nClass Constructor: {cons}\n\n\n"),
    ("ai", "Anwser: Let's do this step by step. {answer}"),
]

EXAMPLES = [
    {
        "code": """
TokenRange withBegin(JavaToken begin) {
    return new TokenRange(assertNotNull(begin), end);
}
""", "deps": """

""", "answer": """
Based on the constructors I have understood before, we can instantiate the parameter `begin`.
According to the constructors, it is easy to instantiate a `begin`. 
`JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken)` can use to instantiate `begin`.
Then we can use "Range(Position begin, Position end)", "Position(int line, int column)" to instantiate hierarchically.
Based on the method signature, body, and constructors, 
we can write instances of `begin` and required import statements to achieve high coverage:
 
Example 1:
    Part 1. The objects initialized:
        ```java
        JavaToken begin = null;
        ```
    
    Part 2. According to the code above, the following import statement must be required:
        ```import
        import com.github.javaparser.JavaToken;
        ```
  
Example 2:
    Part 1. The objects initialized:
        ```java
        Position temp1 = new Position(3, 7);
        Position temp2 = new Position(8, 4);
        Range temp3 = new Range(temp1, temp2);
        JavaToken begin = new JavaToken(temp3, 4, "begin", null, null);
        ```
    
    Part 2. According to the code above, the following import statement must be required:
        ```import
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        ```

Example 3:
    Part 1. The objects initialized:
        ```java
        Position temp1 = new Position(7, 4);
        Position temp2 = new Position(5, 2);
        Range temp3 = new Range(temp1, temp2);
        JavaToken begin = new JavaToken(temp3, 4, "begin", null, null);
        ```
        
    Part 2. According to the code above, the following import statement must be required:
        ```import
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        ```
"""}, {
        "code": """
boolean areInOrder(Node a, Node b, boolean ignoringAnnotations) {
    return compare(a, b, ignoringAnnotations) <= 0;
}
""", "deps": """
  - abstract class: com.github.javaparser.ast.Node
    - Sub classes name:
        - com.github.javaparser.ast.stmt.SwitchEntry
        - com.github.javaparser.ast.stmt.Statement
        - com.github.javaparser.ast.stmt.CatchClause
  - class: com.github.javaparser.ast.stmt.SwitchEntry
    - Constructors:
        - SwitchEntry(final NodeList<Expression> labels, final Type type, final NodeList<Statement> statements): {'statements': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.stmt.SwitchEntry.Type', 'labels': 'com.github.javaparser.ast.NodeList'}
        - SwitchEntry(TokenRange tokenRange, NodeList<Expression> labels, Type type, NodeList<Statement> statements): {'tokenRange': 'com.github.javaparser.TokenRange', 'statements': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.stmt.SwitchEntry.Type', 'labels': 'com.github.javaparser.ast.NodeList'}
        - SwitchEntry(): {}
  - abstract class: com.github.javaparser.ast.stmt.Statement
    - Sub classes name:
        - com.github.javaparser.ast.stmt.BlockStmt
        - com.github.javaparser.ast.stmt.ThrowStmt
        - com.github.javaparser.ast.stmt.LocalClassDeclarationStmt
  - class: com.github.javaparser.ast.stmt.CatchClause
    - Constructors:
        - CatchClause(): {}
        - CatchClause(final Parameter parameter, final BlockStmt body): {'parameter': 'com.github.javaparser.ast.body.Parameter', 'body': 'com.github.javaparser.ast.stmt.BlockStmt'}
        - CatchClause(final NodeList<Modifier> exceptModifier, final NodeList<AnnotationExpr> exceptAnnotations, final ClassOrInterfaceType exceptType, final SimpleName exceptName, final BlockStmt body): {'exceptAnnotations': 'com.github.javaparser.ast.NodeList', 'exceptType': 'com.github.javaparser.ast.type.ClassOrInterfaceType', 'exceptModifier': 'com.github.javaparser.ast.NodeList', 'exceptName': 'com.github.javaparser.ast.expr.SimpleName', 'body': 'com.github.javaparser.ast.stmt.BlockStmt'}
        - CatchClause(TokenRange tokenRange, Parameter parameter, BlockStmt body): {'parameter': 'com.github.javaparser.ast.body.Parameter', 'tokenRange': 'com.github.javaparser.TokenRange', 'body': 'com.github.javaparser.ast.stmt.BlockStmt'}
  - java.util.Stack: a jdk-builtin type or cannot be parsed
  - abstract class: com.github.javaparser.ast.DataKey
  - java.util.IdentityHashMap: a jdk-builtin type or cannot be parsed
  - class: com.github.javaparser.TokenRange
    - Constructors:
        - TokenRange(JavaToken begin, JavaToken end): {'end': 'com.github.javaparser.JavaToken', 'begin': 'com.github.javaparser.JavaToken'}
  - class: com.github.javaparser.Range
    - Constructors:
        - Range(Position begin, Position end): {'end': 'com.github.javaparser.Position', 'begin': 'com.github.javaparser.Position'}
  - interface: com.github.javaparser.printer.configuration.PrinterConfiguration
  - java.util.ArrayList: a jdk-builtin type or cannot be parsed
  - int: a jdk-builtin type or cannot be parsed
  - boolean: a jdk-builtin type or cannot be parsed
  - java.util.Comparator: a jdk-builtin type or cannot be parsed
  - java.util.Iterator: a jdk-builtin type or cannot be parsed
  - abstract class: com.github.javaparser.ast.comments.Comment
    - Sub classes name:
        - com.github.javaparser.ast.comments.BlockComment
        - com.github.javaparser.ast.comments.JavadocComment
        - com.github.javaparser.ast.comments.LineComment
  - com.github.javaparser.ast.Node.Parsedness: a jdk-builtin type or cannot be parsed
  - java.util.Queue: a jdk-builtin type or cannot be parsed
  - class: com.github.javaparser.ast.NodeList
    - Constructors:
        - NodeList(): {}
        - NodeList(N... n): {'n': 'N'}
        - NodeList(Collection<N> n): {'n': 'java.util.Collection'}
  - com.github.javaparser.ast.stmt.SwitchEntry.Type: a jdk-builtin type or cannot be parsed
  - class: com.github.javaparser.ast.stmt.BlockStmt
    - Constructors:
        - BlockStmt(TokenRange tokenRange, NodeList<Statement> statements): {'tokenRange': 'com.github.javaparser.TokenRange', 'statements': 'com.github.javaparser.ast.NodeList'}
        - BlockStmt(): {}
        - BlockStmt(final NodeList<Statement> statements): {'statements': 'com.github.javaparser.ast.NodeList'}
  - class: com.github.javaparser.ast.stmt.ThrowStmt
    - Constructors:
        - ThrowStmt(TokenRange tokenRange, Expression expression): {'expression': 'com.github.javaparser.ast.expr.Expression', 'tokenRange': 'com.github.javaparser.TokenRange'}
        - ThrowStmt(final Expression expression): {'expression': 'com.github.javaparser.ast.expr.Expression'}
        - ThrowStmt(): {}
  - class: com.github.javaparser.ast.stmt.LocalClassDeclarationStmt
    - Constructors:
        - LocalClassDeclarationStmt(final ClassOrInterfaceDeclaration classDeclaration): {'classDeclaration': 'com.github.javaparser.ast.body.ClassOrInterfaceDeclaration'}
        - LocalClassDeclarationStmt(TokenRange tokenRange, ClassOrInterfaceDeclaration classDeclaration): {'tokenRange': 'com.github.javaparser.TokenRange', 'classDeclaration': 'com.github.javaparser.ast.body.ClassOrInterfaceDeclaration'}
        - LocalClassDeclarationStmt(): {}
  - class: com.github.javaparser.ast.body.Parameter
    - Constructors:
        - Parameter(): {}
        - Parameter(Type type, SimpleName name): {'name': 'com.github.javaparser.ast.expr.SimpleName', 'type': 'com.github.javaparser.ast.type.Type'}
        - Parameter(NodeList<Modifier> modifiers, Type type, SimpleName name): {'name': 'com.github.javaparser.ast.expr.SimpleName', 'modifiers': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.type.Type'}
        - Parameter(TokenRange tokenRange, NodeList<Modifier> modifiers, NodeList<AnnotationExpr> annotations, Type type, boolean isVarArgs, NodeList<AnnotationExpr> varArgsAnnotations, SimpleName name): {'varArgsAnnotations': 'com.github.javaparser.ast.NodeList', 'isVarArgs': 'boolean', 'name': 'com.github.javaparser.ast.expr.SimpleName', 'tokenRange': 'com.github.javaparser.TokenRange', 'annotations': 'com.github.javaparser.ast.NodeList', 'modifiers': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.type.Type'}
        - Parameter(NodeList<Modifier> modifiers, NodeList<AnnotationExpr> annotations, Type type, boolean isVarArgs, NodeList<AnnotationExpr> varArgsAnnotations, SimpleName name): {'varArgsAnnotations': 'com.github.javaparser.ast.NodeList', 'isVarArgs': 'boolean', 'name': 'com.github.javaparser.ast.expr.SimpleName', 'annotations': 'com.github.javaparser.ast.NodeList', 'modifiers': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.type.Type'}
        - Parameter(Type type, String name): {'name': 'java.lang.String', 'type': 'com.github.javaparser.ast.type.Type'}
  - class: com.github.javaparser.ast.type.ClassOrInterfaceType
    - Constructors:
        - ClassOrInterfaceType(final ClassOrInterfaceType scope, final SimpleName name, final NodeList<Type> typeArguments, final NodeList<AnnotationExpr> annotations): {'typeArguments': 'com.github.javaparser.ast.NodeList', 'scope': 'com.github.javaparser.ast.type.ClassOrInterfaceType', 'name': 'com.github.javaparser.ast.expr.SimpleName', 'annotations': 'com.github.javaparser.ast.NodeList'}
        - ClassOrInterfaceType(final ClassOrInterfaceType scope, final String name): {'scope': 'com.github.javaparser.ast.type.ClassOrInterfaceType', 'name': 'java.lang.String'}
        - ClassOrInterfaceType(final String name): {'name': 'java.lang.String'}
        - ClassOrInterfaceType(final ClassOrInterfaceType scope, final SimpleName name, final NodeList<Type> typeArguments): {'typeArguments': 'com.github.javaparser.ast.NodeList', 'scope': 'com.github.javaparser.ast.type.ClassOrInterfaceType', 'name': 'com.github.javaparser.ast.expr.SimpleName'}
        - ClassOrInterfaceType(TokenRange tokenRange, ClassOrInterfaceType scope, SimpleName name, NodeList<Type> typeArguments, NodeList<AnnotationExpr> annotations): {'typeArguments': 'com.github.javaparser.ast.NodeList', 'scope': 'com.github.javaparser.ast.type.ClassOrInterfaceType', 'name': 'com.github.javaparser.ast.expr.SimpleName', 'tokenRange': 'com.github.javaparser.TokenRange', 'annotations': 'com.github.javaparser.ast.NodeList'}
        - ClassOrInterfaceType(): {}
  - class: com.github.javaparser.ast.expr.SimpleName
    - Constructors:
        - SimpleName(final String identifier): {'identifier': 'java.lang.String'}
        - SimpleName(TokenRange tokenRange, String identifier): {'identifier': 'java.lang.String', 'tokenRange': 'com.github.javaparser.TokenRange'}
        - SimpleName(): {}
  - class: com.github.javaparser.JavaToken
    - Constructors:
        - JavaToken(int kind): {'kind': 'int'}
        - JavaToken(int kind, String text): {'kind': 'int', 'text': 'java.lang.String'}
        - JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken): {'previousToken': 'com.github.javaparser.JavaToken', 'kind': 'int', 'nextToken': 'com.github.javaparser.JavaToken', 'range': 'com.github.javaparser.Range', 'text': 'java.lang.String'}
  - class: com.github.javaparser.Position
    - Constructors:
        - Position(int line, int column): {'line': 'int', 'column': 'int'}
  - class: com.github.javaparser.printer.configuration.DefaultPrinterConfiguration
    - Constructors:
        - DefaultPrinterConfiguration(): {}
  - class: com.github.javaparser.printer.configuration.PrettyPrinterConfiguration
    - Constructors:
        - PrettyPrinterConfiguration(): {}
  - class: com.github.javaparser.ast.comments.BlockComment
    - Constructors:
        - BlockComment(String content): {'content': 'java.lang.String'}
        - BlockComment(TokenRange tokenRange, String content): {'tokenRange': 'com.github.javaparser.TokenRange', 'content': 'java.lang.String'}
        - BlockComment(): {}
  - class: com.github.javaparser.ast.comments.JavadocComment
    - Constructors:
        - JavadocComment(String content): {'content': 'java.lang.String'}
        - JavadocComment(): {}
        - JavadocComment(TokenRange tokenRange, String content): {'tokenRange': 'com.github.javaparser.TokenRange', 'content': 'java.lang.String'}
  - class: com.github.javaparser.ast.comments.LineComment
    - Constructors:
        - LineComment(String content): {'content': 'java.lang.String'}
        - LineComment(): {}
        - LineComment(TokenRange tokenRange, String content): {'tokenRange': 'com.github.javaparser.TokenRange', 'content': 'java.lang.String'}
  - java.lang.String: a jdk-builtin type or cannot be parsed
  - java.util.List: a jdk-builtin type or cannot be parsed
  - N: a jdk-builtin type or cannot be parsed
  - java.util.ListIterator: a jdk-builtin type or cannot be parsed
  - java.util.Collection: a jdk-builtin type or cannot be parsed
  - abstract class: com.github.javaparser.ast.expr.Expression
    - Sub classes name:
        - com.github.javaparser.ast.expr.AnnotationExpr
        - com.github.javaparser.ast.expr.SuperExpr
        - com.github.javaparser.ast.expr.LambdaExpr
  - class: com.github.javaparser.ast.body.ClassOrInterfaceDeclaration
    - Constructors:
        - ClassOrInterfaceDeclaration(final NodeList<Modifier> modifiers, final NodeList<AnnotationExpr> annotations, final boolean isInterface, final SimpleName name, final NodeList<TypeParameter> typeParameters, final NodeList<ClassOrInterfaceType> extendedTypes, final NodeList<ClassOrInterfaceType> implementedTypes, final NodeList<ClassOrInterfaceType> permittedTypes, final NodeList<BodyDeclaration<?>> members): {'permittedTypes': 'com.github.javaparser.ast.NodeList', 'extendedTypes': 'com.github.javaparser.ast.NodeList', 'implementedTypes': 'com.github.javaparser.ast.NodeList', 'members': 'com.github.javaparser.ast.NodeList', 'name': 'com.github.javaparser.ast.expr.SimpleName', 'annotations': 'com.github.javaparser.ast.NodeList', 'modifiers': 'com.github.javaparser.ast.NodeList', 'isInterface': 'boolean', 'typeParameters': 'com.github.javaparser.ast.NodeList'}
        - ClassOrInterfaceDeclaration(final NodeList<Modifier> modifiers, final boolean isInterface, final String name): {'name': 'java.lang.String', 'modifiers': 'com.github.javaparser.ast.NodeList', 'isInterface': 'boolean'}
        - ClassOrInterfaceDeclaration(TokenRange tokenRange, NodeList<Modifier> modifiers, NodeList<AnnotationExpr> annotations, boolean isInterface, SimpleName name, NodeList<TypeParameter> typeParameters, NodeList<ClassOrInterfaceType> extendedTypes, NodeList<ClassOrInterfaceType> implementedTypes, NodeList<ClassOrInterfaceType> permittedTypes, NodeList<BodyDeclaration<?>> members): {'permittedTypes': 'com.github.javaparser.ast.NodeList', 'extendedTypes': 'com.github.javaparser.ast.NodeList', 'implementedTypes': 'com.github.javaparser.ast.NodeList', 'members': 'com.github.javaparser.ast.NodeList', 'name': 'com.github.javaparser.ast.expr.SimpleName', 'tokenRange': 'com.github.javaparser.TokenRange', 'annotations': 'com.github.javaparser.ast.NodeList', 'modifiers': 'com.github.javaparser.ast.NodeList', 'isInterface': 'boolean', 'typeParameters': 'com.github.javaparser.ast.NodeList'}
        - ClassOrInterfaceDeclaration(): {}
  - abstract class: com.github.javaparser.ast.type.Type
    - Sub classes name:
        - com.github.javaparser.ast.type.VoidType
        - com.github.javaparser.ast.type.PrimitiveType
        - com.github.javaparser.ast.type.UnknownType
  - java.lang.Object: a jdk-builtin type or cannot be parsed
  - java.util.Set: a jdk-builtin type or cannot be parsed
  - java.lang.Class: a jdk-builtin type or cannot be parsed
  - abstract class: com.github.javaparser.ast.expr.AnnotationExpr
    - Sub classes name:
        - com.github.javaparser.ast.expr.NormalAnnotationExpr
        - com.github.javaparser.ast.expr.MarkerAnnotationExpr
        - com.github.javaparser.ast.expr.SingleMemberAnnotationExpr
  - class: com.github.javaparser.ast.expr.SuperExpr
    - Constructors:
        - SuperExpr(Name typeName): {'typeName': 'com.github.javaparser.ast.expr.Name'}
        - SuperExpr(): {}
        - SuperExpr(TokenRange tokenRange, Name typeName): {'tokenRange': 'com.github.javaparser.TokenRange', 'typeName': 'com.github.javaparser.ast.expr.Name'}
  - class: com.github.javaparser.ast.expr.LambdaExpr
    - Constructors:
        - LambdaExpr(NodeList<Parameter> parameters, Statement body, boolean isEnclosingParameters): {'isEnclosingParameters': 'boolean', 'body': 'com.github.javaparser.ast.stmt.Statement', 'parameters': 'com.github.javaparser.ast.NodeList'}
        - LambdaExpr(): {}
        - LambdaExpr(Parameter parameter, BlockStmt body): {'parameter': 'com.github.javaparser.ast.body.Parameter', 'body': 'com.github.javaparser.ast.stmt.BlockStmt'}
        - LambdaExpr(NodeList<Parameter> parameters, BlockStmt body): {'body': 'com.github.javaparser.ast.stmt.BlockStmt', 'parameters': 'com.github.javaparser.ast.NodeList'}
        - LambdaExpr(Parameter parameter, Expression body): {'parameter': 'com.github.javaparser.ast.body.Parameter', 'body': 'com.github.javaparser.ast.expr.Expression'}
        - LambdaExpr(NodeList<Parameter> parameters, Expression body): {'body': 'com.github.javaparser.ast.expr.Expression', 'parameters': 'com.github.javaparser.ast.NodeList'}
        - LambdaExpr(TokenRange tokenRange, NodeList<Parameter> parameters, Statement body, boolean isEnclosingParameters): {'isEnclosingParameters': 'boolean', 'tokenRange': 'com.github.javaparser.TokenRange', 'body': 'com.github.javaparser.ast.stmt.Statement', 'parameters': 'com.github.javaparser.ast.NodeList'}
  - java.util.function.Predicate: a jdk-builtin type or cannot be parsed
  - java.util.function.Function: a jdk-builtin type or cannot be parsed
  - class: com.github.javaparser.ast.type.VoidType
    - Constructors:
        - VoidType(TokenRange tokenRange): {'tokenRange': 'com.github.javaparser.TokenRange'}
        - VoidType(): {}
  - class: com.github.javaparser.ast.type.PrimitiveType
    - Constructors:
        - PrimitiveType(): {}
        - PrimitiveType(TokenRange tokenRange, Primitive type, NodeList<AnnotationExpr> annotations): {'tokenRange': 'com.github.javaparser.TokenRange', 'annotations': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.type.PrimitiveType.Primitive'}
        - PrimitiveType(final Primitive type, NodeList<AnnotationExpr> annotations): {'annotations': 'com.github.javaparser.ast.NodeList', 'type': 'com.github.javaparser.ast.type.PrimitiveType.Primitive'}
        - PrimitiveType(final Primitive type): {'type': 'com.github.javaparser.ast.type.PrimitiveType.Primitive'}
  - class: com.github.javaparser.ast.type.UnknownType
    - Constructors:
        - UnknownType(): {}
        - UnknownType(TokenRange tokenRange): {'tokenRange': 'com.github.javaparser.TokenRange'}
  - class: com.github.javaparser.ast.expr.NormalAnnotationExpr
    - Constructors:
        - NormalAnnotationExpr(TokenRange tokenRange, Name name, NodeList<MemberValuePair> pairs): {'name': 'com.github.javaparser.ast.expr.Name', 'tokenRange': 'com.github.javaparser.TokenRange', 'pairs': 'com.github.javaparser.ast.NodeList'}
        - NormalAnnotationExpr(): {}
        - NormalAnnotationExpr(final Name name, final NodeList<MemberValuePair> pairs): {'name': 'com.github.javaparser.ast.expr.Name', 'pairs': 'com.github.javaparser.ast.NodeList'}
  - class: com.github.javaparser.ast.expr.MarkerAnnotationExpr
    - Constructors:
        - MarkerAnnotationExpr(final Name name): {'name': 'com.github.javaparser.ast.expr.Name'}
        - MarkerAnnotationExpr(final String name): {'name': 'java.lang.String'}
        - MarkerAnnotationExpr(): {}
        - MarkerAnnotationExpr(TokenRange tokenRange, Name name): {'name': 'com.github.javaparser.ast.expr.Name', 'tokenRange': 'com.github.javaparser.TokenRange'}
  - class: com.github.javaparser.ast.expr.SingleMemberAnnotationExpr
    - Constructors:
        - SingleMemberAnnotationExpr(TokenRange tokenRange, Name name, Expression memberValue): {'memberValue': 'com.github.javaparser.ast.expr.Expression', 'name': 'com.github.javaparser.ast.expr.Name', 'tokenRange': 'com.github.javaparser.TokenRange'}
        - SingleMemberAnnotationExpr(): {}
        - SingleMemberAnnotationExpr(Name name, Expression memberValue): {'memberValue': 'com.github.javaparser.ast.expr.Expression', 'name': 'com.github.javaparser.ast.expr.Name'}
  - class: com.github.javaparser.ast.expr.Name
    - Constructors:
        - Name(Name qualifier, final String identifier): {'identifier': 'java.lang.String', 'qualifier': 'com.github.javaparser.ast.expr.Name'}
        - Name(final String identifier): {'identifier': 'java.lang.String'}
        - Name(TokenRange tokenRange, Name qualifier, String identifier): {'identifier': 'java.lang.String', 'qualifier': 'com.github.javaparser.ast.expr.Name', 'tokenRange': 'com.github.javaparser.TokenRange'}
        - Name(): {}
  - com.github.javaparser.ast.type.PrimitiveType.Primitive: a jdk-builtin type or cannot be parsed
  - java.util.HashMap: a jdk-builtin type or cannot be parsed
""", "answer": """
Based on the constructors I have understood before, we can instantiate the parameter `a`, `b` and `ignoringAnnotations`.
According to the constructors, it is easy to instantiate `a`, `b` and `ignoringAnnotations`. 
`com.github.javaparser.ast.Node` can be instantiated via its subclasses "com.github.javaparser.ast.type.UnknownType".
"UnknownType(TokenRange tokenRange)" can specify a range for `comment`.
Then we can use "TokenRange(JavaToken begin, JavaToken end", "JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken)",
"Range(Position begin, Position end)", "Position(int line, int column)" to instantiate hierarchically.
Based on the method signature, body, and constructors, 
we can write instances of `a`, `b` and `ignoringAnnotations` and required import statements to achieve high coverage:
  
Example 1:
    Part 1. The objects initialized:
        ```java
        Node a = null;
        Node b = null;
        boolean ignoringAnnotations = true;
        ```

    Part 2. According to the code above, the following import statement must be required:
        ```import
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
        ```import
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
        ```import
        import com.github.javaparser.ast.Node;
        import com.github.javaparser.ast.type.UnknownType;
        import com.github.javaparser.TokenRange;
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        ```
"""}
]

EXAMPLES_NON_STATIC = [
    {
        "code": """
TokenRange withBegin(JavaToken begin) {
    return new TokenRange(assertNotNull(begin), end);
}
    """, "deps": """
  - class: com.github.javaparser.JavaToken
    - Constructors:
        - JavaToken(int kind): {'kind': 'int'}
        - JavaToken(int kind, String text): {'kind': 'int', 'text': 'java.lang.String'}
        - JavaToken(Range range, int kind, String text, JavaToken previousToken, JavaToken nextToken): {'previousToken': 'com.github.javaparser.JavaToken', 'kind': 'int', 'nextToken': 'com.github.javaparser.JavaToken', 'range': 'com.github.javaparser.Range', 'text': 'java.lang.String'}
  - int: a jdk-builtin type or cannot be parsed
  - class: com.github.javaparser.Range
    - Constructors:
        - Range(Position begin, Position end): {'end': 'com.github.javaparser.Position', 'begin': 'com.github.javaparser.Position'}
  - java.lang.String: a jdk-builtin type or cannot be parsed
  - class: com.github.javaparser.Position
    - Constructors:
        - Position(int line, int column): {'line': 'int', 'column': 'int'}
    """, "answer": """
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
        ```class object
        JavaToken begin = new JavaToken(1);
        JavaToken end = new JavaToken(2);
        TokenRange tokenRange = new TokenRange(begin, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
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
        ```class object
        JavaToken begin = new JavaToken(1, "begin");
        JavaToken end = new JavaToken(2, "end");
        TokenRange tokenRange = new TokenRange(begin, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
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
        ```class object
        JavaToken begin = new JavaToken(1, "begin");
        JavaToken end = new JavaToken(2, "end");
        TokenRange tokenRange = new TokenRange(begin, end);
        ```

    Part 3. According to the code above, the following import statement must be required:
        ```import
        import com.github.javaparser.JavaToken;
        import com.github.javaparser.Range;
        import com.github.javaparser.Position;
        ```
"""}
]

class InputNonUnderstandingChain:
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
                re.finditer(r"- Constructors?:\n(.*?)(?=- Constructors?:\n|$)", text, re.M)]

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

    def init_dict(self, param_dict, param, result) -> str:
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
            if p_info.get("subClassName"):
                result += "    - Sub classes name:\n"
                for name in p_info["subClassName"].values():
                    result += f"        - {name}\n"
                for name in p_info["subClassName"].values():
                    result = self.init_dict(param_dict, name, result)
            if p_info.get("subInterfaceName"):
                result += "    - Implementation classes name:\n"
                for name in p_info["subInterfaceName"].values():
                    result += f"        - {name}\n"
                for name in p_info["subInterfaceName"].values():
                    result = self.init_dict(param_dict, name, result)
            if p_info.get("constructors"):
                result += "    - Constructors:\n"
                for (signature, params) in p_info["constructors"].items():
                    result += f"        - {signature}: {params}\n"
        return result

    def run(self, spec, mg_dict: dict):
        # Clear all cache information
        self.cons = ""
        self.types = set()
        param_list = util.mg_util.parameter_info(mg_dict, layer=10)

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

        # Generate test cases
        if mg_dict["static"]:
            messages = self.generator_prompt.format_messages(code=mg_dict["code"], spec=spec, deps=param_list)
        else:
            messages = self.generator_non_static_prompt.format_messages(code=mg_dict["code"], spec=spec,
                                                                        deps=param_list,
                                                                        cons=constructor_str)
        for message in messages:
            print(f"\33[32m{message.content}\033[0m\n")
        llm_result: LLMResult = self.llm.generate([messages])
        return {
            "java": self.parse_java(llm_result),
            "cons": self.parse_cons(llm_result),
            "import": self.parse_import(llm_result)
        }


if __name__ == "__main__":
    from config import *

    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0)
