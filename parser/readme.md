To run this program download the IG-Parser repo available at:
https://github.com/chrfrantz/IG-Parser

Then move the "main.go" file from this folder to the root folder of the repository.

Finally, run the command 'go run main.go'.

This will spin up a rest api which takes an annotated statement and returns a json object
which includes the amount of and the contents of the following components:

* Attribute
* Direct Object
* Indirect Object
* Deontic
* Aim

This is used to evaluate the performance of the matching function for automated parsing.

The other option is to use the "autoRunner.go".

This program also requires the IG-Parser and should be moved into the IG-Parser folder.

It can be run by running the command 'go run main.go'

Additionally, it requires an "input.json" file with the structure:

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

This program writes the detected components to the same file in the form of JSON objects which can be used to compare.

Both these solutions have the same formatting, but further development is required to make them more usefull for comparison, and additionally manually checking the difference is recommended.