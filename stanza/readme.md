# Stanza test functions

This folder contains test functions in stanza to test the functionality (of both stanza and stanford corenlp through the stanza interface).

To install the dependencies run

`pip install -r requirements.txt`

I recommend using a virtual environment.

Tested using Python 3.11

Afterwards Stanford CoreNLP has to be installed. This can be done through running `installCoreNLP.py`.
After it is done a corenlp folder should appear in this directory. This directory needs to be added to the `CORENLP_HOME` environment variable.

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
Additionally, the input data for the dependency tree is added to a table and displayed in the terminal and
named entities and a constituency tree are printed to the console.
The displacy visualizer is used to show the tree, which is hosted locally on "localhost:5000".