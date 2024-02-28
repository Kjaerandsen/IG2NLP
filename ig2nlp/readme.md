# IG2NLP

This folder contains programs for automating the annotation of institutional statements with the
Institutional Grammar notation using NLP tools and a matching function.

To install the dependencies run

`pip install -r requirements.txt`

Alternatively see the dependencies section below.

I recommend using a virtual environment.

Tested using Python 3.11, models and programs used do not support Python 3.12 as of the time of writing.

## Python programs:

### ig2nlp.py

Takes an integer in the form

`python ig2nlp.py 0`

The integer is the id of the statement which the program automatically annotates. 
A value of negative 1 (-1) goes through all statements instead.
This statement is located in a JSON object in the file 
`input.json`, where the JSON data has the structure:

```
[
  {
    "name": "Custom name for the statement",
    "baseTx": "Base statement text",
    "manuTx": "Manually annotated statement",
    "autoTx": "Automatically annotated statement using stanza",
  },
]
```

The program saves the automatically annotated statement to the "stanza" key of the input statement.

### dependencyParsing.py
Takes a string in the form:

`python dependencyParsing.py "input string here"`

The program then uses displacy to create a dependency tree based on the input.
Additionally, the input data for the dependency tree is added to a table 
and displayed in the terminal and named entities and a constituency tree are 
printed to the console.
The displacy visualizer is used to show the tree, which is hosted locally on "localhost:5000".

### dependencyParsingFromRest.py

Takes a string in the form:

`python dependencyParsingFromRest.py "input string here"`

The program then uses displacy to create a dependency tree based on the input.
Additionally, the input data for the dependency tree is added to a table 
and displayed in the terminal and named entities and a constituency tree are 
printed to the console.
The displacy visualizer is used to show the tree, which is hosted locally on "localhost:5000".

This version of the program uses the rest api exposed by the `restPipeline.py` program.

### restPipeline.py

Run with: 

`flask --app .\restPipeline.py run -p 5000`

The port can be changed by altering the -p parameter.

Requires first commenting out the "__slots__" variable in the Word class in `utility.py`.
The program opens a rest api that can handle the nlp pipeline tasks for the `dependencyParsingFromRest.py`
and the `runner.py` programs for testing and development purposes. Due to the startup time for loading the models
this is faster for single statements than loading it in the programs themselves.

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

Dependencies are Stanza, Spacy and Pandas.
They can be installed using the commands:

```
pip install stanza 
pip install spacy
pip install pandas
pip install pyarrow
pip install transformers
pip install peft
pip install flask
pip install requests
pip install python-dotenv
pip install pytest
pip install pytest-cov
```

Tested on Stanza v1.7.0, newer versions may not work as expected.

Further for GPU processing Cuda is required, and PyTorch with Cuda.
See `https://pytorch.org/get-started/locally/`.