import json
import argparse
import numpy as np
import pandas as pd

from testbed.comparison import *
from testbed.componentStatistics import *

def main() -> None:
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", 
      help="input file, defaults to json extension, i.e. input is treated as input.json")
   parser.add_argument("-o", "--output", 
      help="output file, defaults to json extension, i.e. output is treated as output.json")
   parser.add_argument("-m", "--mode",
      help="mode of the program, defaults to the whole testing pipline ignoring nesting. For more info\
   refer to the readme file.", default=30, type=int)
   args = parser.parse_args()

   if not args.input:
      filename = "../data/output.json"
   else:
      filename = "../data/"+args.input+".json"

   if not args.output:
      outfilename = "../data/output"
   else:
      outfilename = "../data/"+args.output

   mode = args.mode

   with open(filename, "r") as input:
      jsonData = json.load(input)

   match mode:
      case 0:
         print("Mode 0")
      case 1:
         compare(jsonData, outfilename)
      case 2:
         print("Mode 2")

def compare(jsonData:dict, outfilename:str) -> None:
   compNames = ["A,p","Bdir","Bdir,p","Bind","Bind,p","Cac",
                "Cex","E,p","P","P,p","O","A","D","I","E","M","F"]
   outData:list[dict] = []

   totalMatches = np.zeros((17,5), dtype=int)
   for statement in jsonData:
      matches = np.zeros((17,5), dtype=int)
      #print(statement["name"])
      #print(statement["stanzaParsed"])

      """
      Compare components for direct matches 
      I.e. x(content) == x(content)
      """
      partialPool = []
      
      #True positive scope and symbol, also accounts for invalid nesting
      matches = compareComponentsDirect(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      
      # True positive scope, wrong symbol
      matches = compareComponentsWrongSymbol(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      
      # Partial content matches
      matches = compareComponentsPartial(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      
      # Count the non-matched components as False Positives from auto, and False Negatives from manu
      matches = countFPandFN(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches)
      
      # Count the total amount of matches in each category (TP, PP, FP, FN) for each component type
      matches = countTotal(matches)

      # Add this statements matches to the total
      totalMatches += matches
      statementData = dict()
      
      statementData["Count"] = []
      count = matches.tolist()
      for j in range(17):
         matchData=compNames[j]+(6-len(compNames[j]))*" "+": "+str(count[j][0])
         for k in range(4):
            matchData+=","+str(count[j][k+1])
         statementData["Count"].append(matchData)
         
      #statementData["Count"]=matches.tolist()

      for dataPoint in ["name","baseTx","manuTx","autoTx"]:
         statementData[dataPoint] = statement[dataPoint]
      statementData["extraComponents"] = dict()
      # Combine all components to a pool of extra components
      statementData["extraComponents"]["manuTx"] = combineComponents(
         statement["manualParsed"]["components"])
      statementData["extraComponents"]["autoTx"] = combineComponents(
         statement["stanzaParsed"]["components"])
      statementData["partialPool"] = partialPool
      outData.append(statementData)
   
   print(matches,"\n")

   # Write all partial matches, extra components and individual statement counts
   with open(outfilename+".json", "w") as output:
      json.dump(outData, output, indent=2)
   
   # Write the totals in each category to a separate total file
   # Create a dataframe (table) of the match statistics
   df = pd.DataFrame(columns=["Symbol", "TP", "PP", "FP", "FN", "Total"])
   """
   compNames = ["Attribute Property", "Direct Object", "Direct Object Property", "Indirec Object",
                "Indirect Object Property", "Activation Condition", "Execution Contraint",
                "Constituted Entity Property", "Constituting Properties", 
                "Constituting Properties Property", "Or Else", "Attribute", "Deontic", "Aim",
                "Contituted Entity", "Modal", "Constitutive Function"]
   """
   for i in range(17):
      df = df._append({
         "Symbol":compNames[i], 
         "TP":int(totalMatches[i][0]),
         "PP":int(totalMatches[i][1]), 
         "FP":int(totalMatches[i][2]), 
         "FN":int(totalMatches[i][3]), 
         "Total":int(totalMatches[i][4])
      },ignore_index=True)

   df = df.sort_values(by=['Symbol'])

   #print(df)
   # Create totals
   with open(outfilename+"Total.txt", "w") as output:
      output.write(str(df))


main()