# Stanza test functions

This folder contains test functions in stanza to test the functionality 
(of both stanza and stanford corenlp through the stanza interface).

To install the dependencies run

`pip install -r requirements.txt`

Alternatively see the dependencies section below.

I recommend using a virtual environment.

Tested using Python 3.11, models used do not support Python 3.12 as of the time of writing.

Afterwards Stanford CoreNLP has to be installed. 
This can be done through running `installCoreNLP.py`.
After it is done a corenlp folder should appear in this directory. T
his directory needs to be added to the `CORENLP_HOME` environment variable.

## Python programs:

### coreferenceResolution.py
Takes a string in the form:

`python coreferenceResolution.py "input string here"`

The program then prints out the mentions of the objects in the text as well as the coref chains 
which describes the connection between the objects.

### dependencyParsing.py
Takes a string in the form:

`python dependencyParsing.py "input string here"`

The program then uses displacy to create a dependency tree based on the input.
Additionally, the input data for the dependency tree is added to a table 
and displayed in the terminal and named entities and a constituency tree are 
printed to the console.
The displacy visualizer is used to show the tree, which is hosted locally on "localhost:5000".

### runner.py

Old version of the automated annotator.

Takes an integer in the form

`python runner.py 0`

The integer is the id of the statement which the runner automatically annotates. 
This statement is located in a JSON object in the file 
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

The runner saves the automatically annotated statement to the "stanza" key of the input statement.

### runnerAdvanced.py

New version of the annotator.

Takes an integer in the form

`python runnerAdvanced.py 0`

The integer is the id of the statement which the runner automatically annotates. 
A value of negative 1 (-1) goes through all statements instead.
This statement is located in a JSON object in the file 
`input.json`, where the JSON data has the structure:

```
[
  {
    "name": "Custom name for the statement",
    "baseTx": "Base statement text",
    "manual": "Manually annotated statement",
    "stanza": "Automatically annotated statement using stanza",
  },
]
```

The runner saves the automatically annotated statement to the "stanza" key of the input statement.

### parseTrees.py

Opens `input.json` with the structure:

```
[
  {
    "name": "Custom name for the statement",
    "baseTx": "Base statement text",
    ...
  },
]
```

Goes through all base statement texts and creates displacy visualizations of 
their dependency parse trees. These trees are written to html documents in the data directory.

### pipelineData.py

Opens `input.json` with the structure:

```
[
  {
    "name": "Custom name for the statement",
    "baseTx": "Base statement text",
    ...
  },
]
```

Goes through all base statement texts, runs a Stanza pipeline on the statement texts and writes
the data to tables in a pipeline.txt file.

## Dependencies

Dependencies are Stanza, Spacy and Pandas. They can be installed using the command:

```
pip install stanza 
pip install spacy
pip install pandas
pip install pyarrow
pip install transformers
pip install peft
```

Further for GPU processing Cuda is required, and PyTorch with Cuda.
See `https://pytorch.org/get-started/locally/`.