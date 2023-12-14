To run this program download the IG-Parser repo available at:
https://github.com/chrfrantz/IG-Parser

Then move the main.go file from this folder to the root folder of the repository.

Finally, run the command 'go run main.go'.

This will spin up a rest api which takes an annotated statement and returns a json object
which includes the amount of and the contents of the following components:

* Attribute
* Direct Object
* Indirect Object
* Deontic
* Aim

This is used to evaluate the performance of the matching function for automated parsing.