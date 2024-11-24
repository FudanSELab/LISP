# LLMISP

## llm-seed-generator

* Python: 3.10

### 1. Build seed generator

```shell
cd llm-seed-generator

# create virtual environment
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## llm-jqf

* Java: 11
* Build system: Maven

### 1. Build jqf-llm

```shell
# ./llm-JQF
mvn install -DskipTests
```

### 2. Run

```shell
cd llm-JQF

# run jqf-llm via submitting the package name and signature of method
bin/jqf-llm -i -o "org.apache.commons:commons-lang3:3.14.0" "org.apache.commons.lang3.StringUtils.indexOfDifference(CharSequence,CharSequence)"
```
