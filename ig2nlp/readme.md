# IG2NLP

This folder contains programs for automating the annotation of institutional statements with the
Institutional Grammar notation using NLP tools and a matching function.

To install the dependencies run

`pip install -r requirements.txt`

Alternatively see the dependencies section below.

I recommend using a virtual environment for Python.

Tested using Python 3.11, models and programs used do not support Python 3.12 as of the time of writing.

## Docker api
* Create the stanza_resources folder if not already present: `mkdir ~/stanza_resources`
(make a  folder named "stanza_resources" in the home directory)

* Start the container with: `docker compose up`

* Alternatively build the container from the dockerfile and run it manually. A shared volume for stanza_resources is recommended to reuse the models.

Requests are in the form of REST POST requests to the /ig2nlp endpoint on port 5000 by default.
The requests are JSON requests with the structure:

```
[{
	"stmtId": "1",
	"origStmt": "word",
	"apiVersion": 0.1,
	"matchingParams": {
		"coref":true, 
		"semantic":true,
		"semanticNumber":true
	}
}]
```

The response structure is:

```
[{
    "apiVersion": 0.1,
    "commentConst": "",
    "commentReg": "",
    "encodedStmtConst": "F(word).",
    "encodedStmtReg": "I(word).",
    "matchingParams": {
        "coref": true,
        "semantic": true,
        "semanticNumber": true
    },
    "origStmt": "Attribute.",
    "stmtId": "1"
}]
```

With comments for manual review of the annotations for both constitutive and regulative annotations.
The response includes both a constitutive and a regulative annotation of the input statement(s).


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

This program also allows for several parameters for different functionality. 
These parameters are the following:

1. id (default number)
2. -i or --input
3. -s or --single
4. -c or --constitutive
5. -r or --reuse
6. -b or --batch
7. -o or --output

The input and output take filenames in the form of strings, defaults to appending a ".json" file extension to the end of the input string.

The id is the single unmarked integer as seen in the example above, it refers to a statement id in the dataset, i.e. 0 would be the first statement in the dataset used, defaults to running every statement if undefined.

The single, constitutive and reuse all are flags that enable their individual features. Single sets the batch size to one, constitutive makes the automated annotater handle statements as constitutive instead of the default of handling them as regulative and reuse uses cached NLP pipeline data created with the "cache.py" program. 

Finally, the batch parameter enables changing the batch size to any integer, the batch size is the amount of statements ran through the NLP pipeline per batch. Defaults to running 30 statements per batch, however depending on memory constraints and dataset sizes a smaller batch size may be preferable. Also due to a bug in the coreference resolution model used the pipeline may in some cases cause errors that can be mitigated through running with a batch size of one, or with the "single" parameter.

A complete example of running the ig2nlp.py can be seen below:

`python ig2nlp.py -cri "input" -o "output"`

### dependencyParsing.py
Takes a string in the form:

`python dependencyParsing.py "input string here"`

The program then uses displacy to create a dependency tree based on the input.
Additionally, the input data for the dependency tree is added to a table 
and displayed in the terminal and named entities and a constituency tree are 
printed to the console.
The displacy visualizer is used to show the tree, which is hosted locally on "localhost:5000".

### parseTrees.py

Opens `input.json` with the structure defined in the segment on "ig2nlp.py".

Goes through all base statement texts and creates displacy visualizations of 
their dependency parse trees. These trees are written to html documents in the data directory.

This program shares the input, single and batch parameters with the "ig2nlp.py" program.

### pipelineData.py

Opens `input.json` with the structure defined in the segment on "ig2nlp.py".

Goes through all base statement texts, runs a Stanza pipeline on the statement texts and writes the data to tables in a pipeline.txt file. The data contains different NER model results, POS-tagging, XPOS-tagging, u-Feats data and more.

### testBed.py

TestBed is a program for comparing automated annotation with a comparison, it compares the component annotations of two sets of annotations at four levels. Direct comparison with true positives, partial positives where there is a partial match between the control and the automated annotation, and finally false positives and false negatives for components not in the previous two categories. This comparison is automated, however the automation is limited and manual review of the component matches is advised.

Opens `input.json` with the structure defined in the segment on "ig2nlp.py".

Takes input and output parameters as described in the segment on "ig2nlp.py". Also takes a -m or --mode parameter and -n or --nested parameter.
The nested parameter enables handling of nested component structures, the mode switches between four modes (0-3):

0. Mode 0 performs both component extraction and comparison.
1. Mode 1 performs component extraction.
2. Mode 2 performs comparison, (relies on the output of the mode 1).
3. Mode 3 performs component extraction and creates an additional text file with counts of each component type.

The component extraction takes an input file in the default input format as described in the other sections. The output is a JSON document with the components of each statement divided into components in the manual annotation and the automated annotation. This is used as the input for the "comparison" mode which outputs a final count of component matches and a JSON file with the structure:

[
  {
    "Count": [
      "A,p   : 0,0,0,0,0",
      "Bdir  : 0,0,0,0,0",
      "Bdir,p: 0,0,0,0,0",
      "Bind  : 0,0,0,0,0",
      "Bind,p: 0,0,0,0,0",
      "Cac   : 0,0,0,0,0",
      "Cex   : 0,0,0,0,0",
      "E,p   : 0,0,0,0,0",
      "P     : 0,0,0,0,0",
      "P,p   : 0,0,0,0,0",
      "O     : 0,0,0,0,0",
      "A     : 0,1,0,0,1",
      "D     : 0,0,0,0,0",
      "I     : 0,0,0,0,0",
      "E     : 0,0,0,0,0",
      "M     : 0,0,0,0,0",
      "F     : 0,0,0,0,0"
    ],
    "name": "St. 1",
    "baseTx": "Union",
    "manuTx": "A(Union States)",
    "autoTx": "A(Union) A,p(States)",
    "extraComponents": {
      "manuTx": [],
      "autoTx": []
    },
    "partialMatches": [
      "manuTxComponents": [
          {
            "Content": "Union States",
            "Nested": false,
            "componentType": "A"
          }
      ],
      "autoTxComponents": [
          {
            "Content": "Union",
            "Nested": false,
            "componentType": "A"
          },
          {
            "Content": "States",
            "Nested": false,
            "componentType": "A,p"
          }
      ]
    ]
  }
]

This file contains a list of components partially matched, and not matched for comparing the manual and automated annotations of statements in a dataset. The count refers to the amount of components of a certain type that are true positives, partial positives, false positives, false negatives and a total respectively.

### cache.py

Opens input file specified with the input parameter with the structure defined in the segment on "ig2nlp.py". Runs the NLP pipeline and caches the results for every statement in the dataset. Used as the basis for the -r parameter of the "ig2nlp.py" program.

This program shares the input, single and batch parameters with the "ig2nlp.py" program.

### api.py

The same program as described in the section on above on the docker api. All parameters for the api are defined through the .env file. For an example look at the "dotenvExample" file. To use such configuration options create a file named ".env" in the "data" directory with the same structure as the dotenvExample file.

### apiTest.py

Basic test program for the api, sends requests with a random amount of statements (1-5) to the api in a continuous loop. Takes an input file parameter with the same structure as programs outlined above.

## Dependencies

The dependencies are all located in the "requirements.txt" file and can be installed using the command:

`pip install -r requirements.txt`

Tested on Stanza v1.8.1, newer versions may not work as expected.

Further for GPU processing Cuda is required, and PyTorch with Cuda must be manually installed in addition to the requirements in the requirements.txt file.
See `https://pytorch.org/get-started/locally/`.