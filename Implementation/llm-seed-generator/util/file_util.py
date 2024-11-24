def write_dict(input_dict: dict, is_static: bool):
    result = ""
    for value in input_dict.values():
        input_generation = value["java"]
        class_object = value["cons"]
        import_statement = value["import"]
        for i in range(len(input_generation)):
            result += "Part1:"
            result += input_generation[i]
            result += "\nPart2:"
            if not is_static:
                if i < len(class_object):
                    result += class_object[i]
            result += "\nPart3:"
            if i < len(import_statement):
                result += import_statement[i]
            result += "\n---------------\n"

    with open('../input_generator', 'w') as f:
        f.write(result)


if __name__ == "__main__":
    test_dict = {'1. `startIndex`: is negative; 2. `endIndex`: can be any integer': {'java': ['int startIndex = -5;\n        int endIndex = 10;', 'import org.apache.commons.lang3.text.StrBuilder;', 'int startIndex = -3;\n        int endIndex = 5;', 'import java.lang.String;\n        import org.apache.commons.lang3.text.StrBuilder;'], 'cons': ['int initialCapacity = 20;\n        StrBuilder strBuilder = new StrBuilder(initialCapacity);', 'String str = "Hello";\n        StrBuilder strBuilder = new StrBuilder(str);']}, '1. `startIndex`: is greater than or equal to the length of the `StrBuilder` object; 2. `endIndex`: can be any integer': {'java': ['int startIndex = 5;\n        int endIndex = 10;', 'import org.apache.commons.lang3.text.StrBuilder;', 'int startIndex = 0;\n        int endIndex = 15;', 'import java.lang.String;\n        import org.apache.commons.lang3.text.StrBuilder;'], 'cons': ['int initialCapacity = 20;\n        StrBuilder strBuilder = new StrBuilder(initialCapacity);', 'String str = "Hello World";\n        StrBuilder strBuilder = new StrBuilder(str);']}, '1. `startIndex`: is less than the length of the `StrBuilder` object; 2. `endIndex`: is less than or equal to `startIndex`': {'java': ['int startIndex = 2;\n        int endIndex = 2;', 'import org.apache.commons.lang3.text.StrBuilder;', 'int startIndex = 0;\n        int endIndex = 3;', 'import java.lang.String;\n        import org.apache.commons.lang3.text.StrBuilder;'], 'cons': ['int initialCapacity = 10;\n        StrBuilder strBuilder = new StrBuilder(initialCapacity);', 'String str = "Hello";\n        StrBuilder strBuilder = new StrBuilder(str);']}, '1. `startIndex`: is less than the length of the `StrBuilder` object; 2. `endIndex`: is greater than `startIndex` and less than the length of the `StrBuilder` object': {'java': ['int startIndex = 2;\n        int endIndex = 5;', 'import org.apache.commons.lang3.text.StrBuilder;', 'int startIndex = 0;\n        int endIndex = 3;', 'import org.apache.commons.lang3.text.StrBuilder;'], 'cons': ['StrBuilder strBuilder = new StrBuilder("Hello World");', 'StrBuilder strBuilder = new StrBuilder("Java");']}, '1. `startIndex`: is less than the length of the `StrBuilder` object; 2. `endIndex`: is greater than or equal to the length of the `StrBuilder` object': {'java': ['int startIndex = 0;\n        int endIndex = 5;', 'import org.apache.commons.lang3.text.StrBuilder;', 'int startIndex = 2;\n        int endIndex = 10;', 'import org.apache.commons.lang3.text.StrBuilder;'], 'cons': ['StrBuilder strBuilder = new StrBuilder("Hello World");', 'StrBuilder strBuilder = new StrBuilder();']}}
    write_dict(test_dict, False)
