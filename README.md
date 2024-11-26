# LISP

> This repository contains the source code of LISP and tables of data recorded in the experiments.

ICSE '25: LLM Based Input Space Partitioning Testing for Library APIs

Jiageng Li, Zhen Dong*, Chong Wang, Haozhen You, Cen Zhang, Yang Liu, Xin Peng

## Link for Experiments Results: [<u>https://FudanSELab.github.io/LISP</u>](https://FudanSELab.github.io/LISP)

This link contains the information of the evaluation in our experiments.

## How to use LISP

1. Prerequisites
    - A java library that exists in maven central repository.
    - A valid OpenAI API Key.
    - Java 11 & Python 3.10 & Maven 9.

2. Usage
    - Create a file named `llm-seed-generator.cfg` in the folder `llm-seed-generator`, refer to the file `llm-seed-generator.example.cfg` for details, and replace the **OPENAI_KEY** in it with your valid OpenAI API Key.

    - Add the java library you want to test to the **dependencies** in the `pom.xml` file in the folder `llm-JQF/fuzz`.

    - Run `mvn install -DskipTests` in the folder `llm-JQF`.

    - Run `bin/jqf-llm -i -o {library_name} {api_name}` in the folder `llm-JQF`.

    - **library_name**'s format: `group_id:artifact_id:version`

      **api_name**'s format: `class_name.method_name(param_type_names)`

      _EX._ `bin/jqf-llm -i -o "org.apache.commons:commons-lang3:3.14.0" "org.apache.commons.lang3.StringUtils.indexOfDifference(CharSequence,CharSequence)"`
