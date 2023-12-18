import json
import sys
from matcherAsFunction import Matcher

args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\ndependencyParsing "Input string here"')
    sys.exit()

number = int(args[1])

filename = "input.json"

# The testData.json is a json file containing an array of objects with a name, baseText and processedText.
# The important fields are the baseText which is the input statement and the processedText which is the 
# annotated statement.
with open(filename, "r") as input:
    jsonData = json.load(input)
    print(jsonData[number])

#print(jsonData[number]['baseText'])

output = Matcher(jsonData[number]['baseText'])

print(jsonData[number]['baseText'] + "\n" + jsonData[number]['processedText'] + "\n" + output)

jsonData[number]["stanza"] = output

# Write the automatically parsed statement to the file
with open(filename, "w") as outputFile:
    json.dump(jsonData, outputFile, indent=2)

