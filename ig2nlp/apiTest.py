import requests
import json
import argparse
import random
import time

parser = argparse.ArgumentParser()

args = parser.parse_args()
parser.add_argument("-i", "--input", 
   help="input file, defaults to json extension, i.e. input is treated as input.json",
   default="input")
parser.add_argument("-o","--output", 
   help="output file, defaults to json extension, i.e. output is treated as output.json")
args = parser.parse_args()

filename:str = "../data/"+args.input+".json"

if args.output:
   outfilename:str = "../data/"+args.output+".json"
else:
   outfilename:str = filename

# Open input file
with open(filename, "r") as input:
   jsonData = json.load(input)

# Get the length of the inputs
jsonLen = len(jsonData)

random.seed(version=2)

# Loop infinitely
while True:
   # Take a random set of statements
   statementCount = random.randrange(1,5)
   statementStart = random.randrange(0,jsonLen-statementCount-1)

   requestStatements = []
   for i in range(statementCount):
      id = i + statementStart
      # Convert the format
      statementData = {}
      statementData["stmtId"] = jsonData[id]["name"]
      statementData["origStmt"] = jsonData[id]["baseTx"]
      statementData["apiVersion"] = 0.1
      # Give the statements random parameters

      # Append to the requestStatements
      requestStatements.append(statementData)
   
   start = time.monotonic()
   # Send a request
   r = requests.post("http://127.0.0.1:5000/ig2nlp", json=requestStatements)
   #print(json.dumps(requestStatements))
   executionTime = time.monotonic() - start
   print("Request time per statement: ", str("%.2f" % (executionTime/statementCount)),"s", " | total: ",
           str("%.2f" % executionTime),"s", "\nAmount of statements: ", statementCount)
   if r.status_code != 200:
      print("Error, not 200 response: ", r.status_code)
      print(r.json())
      break

   #response = r.json()
   #for data in response:
   #   print(data["encodedStmtReg"])

   # Check the resulting data

   # Print the time spent on the input divided by the number of statements and a count of statements
   # Perhaps also average statement length