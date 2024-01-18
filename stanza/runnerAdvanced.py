import json
import sys
from matcherAsFunctionAdvanced import Matcher

args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\ndependencyParsing "Input string here"')
    sys.exit()

number = int(args[1])

filename = "input.json"

i = number

# The testData.json is a json file containing an array of objects with a name, baseText and processedText.
# The important fields are the baseText which is the input statement and the processedText which is the 
# annotated statement.
with open(filename, "r") as input:
    jsonData = json.load(input)

# If argument is -1 then go through all the items
if i == -1:
    i = 0

    print("Running with ", len(jsonData), " items.")
    while i < len(jsonData): 
        

        
        output = Matcher(jsonData[i]['baseText'])

        print(jsonData[i]['baseText'] + "\n" + jsonData[i]['processedText'] + "\n" + output)

        jsonData[i]["stanza"] = output

        # Write the automatically parsed statement to the file
        #with open(filename, "w") as outputFile:
        #    json.dump(jsonData, outputFile, indent=2)

        i += 1

    # Write the automatically parsed statement to the file
    with open(filename, "w") as outputFile:
        json.dump(jsonData, outputFile, indent=2)

# Else only go through the selected item
else:
    #print(jsonData[i]['baseText'])

    output = Matcher(jsonData[i]['baseText'])

    print(jsonData[i]['baseText'] + "\n" + jsonData[i]['processedText'] + "\n" + output)

    jsonData[i]["stanza"] = output

    # Write the automatically parsed statement to the file
    with open(filename, "w") as outputFile:
        json.dump(jsonData, outputFile, indent=2)
            
    #    i += 1

