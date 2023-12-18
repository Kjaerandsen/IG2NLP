# Spacy test functions

This folder contains test functions in spacy to test the functionality.

To install the dependencies run

`pip install -r requirements.txt`

I recommend using a virtual environment.

Tested using Python 3.11

## Python programs:

### coreferenceResolution.py
Takes a string in the form:

`python coreferenceResolution.py "input string here"`

The program then prints out the coref clusters. Which is a set of clusters of references to the same object.
Additionally, the spans of each reference is returned. Which shows where the references appear in the input text.

### dependencyParsing.py
Takes a string in the form:

`python dependencyParsing.py "input string here"`

The program then uses displacy to create a dependency tree based on the input.
Additionally, the input data for the dependency tree is added to a table and displayed in the terminal.
The displacy visualizer is used to show the tree, which is hosted locally on "localhost:5000".

### runner.py
Takes an integer in the form

`python runner.py 0`

The integer is the id of the statement which the runner automatically annotates. This statement is located in a JSON object in the file 
`input.json`, where the JSON data has the structure:

```
[
  {
    "name": "Custom name for the statement",
    "baseText": "Base statement text",
    "processedText": "Manually annotated statement",
    "stanza": "Automatically annotated statement using stanza",
    "spacy": "Automatically annotated statement using spacy"
  },
]
```

The runner saves the automatically annotated statement to the "spacy" key of the input statement.