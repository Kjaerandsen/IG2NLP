import json
from matchingFunction import MatcherMiddleware
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("id", 
    help="Id from the input to run through the parser, -1 goes through all statements")
parser.add_argument("-i", "--input", 
    help="input file, defaults to json extension, i.e. input is treated as input.json")
args = parser.parse_args()

number = int(args.id)

if not args.input:
    filename = "../data/input.json"
else:
    filename = "../data/"+args.input+".json"

i = number

# The testData.json is a json file containing an array of objects 
# with a name, baseText and processedText.
# The important fields are the baseText which is the input statement 
# and the processedText which is the annotated statement.
with open(filename, "r") as input:
    jsonData = json.load(input)

# If argument is -1 then go through all the items
if i == -1:
    i = 0

    print("Running with ", len(jsonData), " items.")
    
    jsonData = MatcherMiddleware(jsonData)

    # Write the automatically parsed statement to the file
    with open(filename, "w") as outputFile:
        json.dump(jsonData, outputFile, indent=2)

# Else only go through the selected item
else:
    #print(jsonData[i]['baseText'])
    if i >= len(jsonData):
        print("Error, the index provided is higher than "+
              "or equal to the amount of items in the input data.")
    else:
        jsonData[i] = MatcherMiddleware(jsonData[i:i+1])[0]

    # Write the automatically parsed statement to the file
    with open(filename, "w") as outputFile:
        json.dump(jsonData, outputFile, indent=2)
            
    #    i += 1

