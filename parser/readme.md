To run this program download the IG-Parser repo available at:
https://github.com/chrfrantz/IG-Parser

The programs can then be run through either adding the repository above to your goroot directory, or by moving the files in this directory to the root of the downloaded repository and running them.

The command 'go run main.go' can be used to run the program.

This will spin up a rest api which takes an annotated statement and returns a json object
which includes the amount of and the contents of the following components:

* Attribute
* Direct Object
* Indirect Object
* Activation Condition
* Execution Constraint
* Deontic
* Aim

This is used to evaluate the performance of the matching function for automated parsing.

The other option is to use the "autoRunner.go".

This program has the same requirements as the one above, additionally, it requires an "input.json" file with the structure:

'''
[
    {
        "name": "Custom id for the statement, any string",
        "baseText": "Base text not encoded",
        "processedText": "Manually annotated text for comparrison",
        "stanza": "Automatically annotated statement",
        "spacy": "Automatically annotated statement"
    }
]
'''

It can be run by running the command 'go run autoRunner.go'

This program writes the detected components to the same file in the form of JSON objects which can be used to compare.

Both these solutions have the same formatting, but further development is required to make them more usefull for comparison, and additionally manually checking the difference is recommended.