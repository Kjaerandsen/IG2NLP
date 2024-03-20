import json
import argparse
import numpy as np

def main() -> None:

   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", 
      help="input file, defaults to json extension, i.e. input is treated as input.json")
   parser.add_argument("-o", "--output", 
      help="output file, defaults to json extension, i.e. output is treated as output.json")
   args = parser.parse_args()

   if not args.input:
      filename = "../data/output.json"
   else:
      filename = "../data/"+args.input+".json"

   if not args.output:
      outfilename = "../data/output.json"
   else:
      outfilename = "../data/"+args.output+".json"

   with open(filename, "r") as input:
      jsonData = json.load(input)

   outData:list[dict] = []

   matches = np.zeros((17,5), dtype=int)
   for statement in jsonData:
      #print(statement["name"])
      #print(statement["manualParsed"])
      #print(statement["stanzaParsed"])

      # Compare components for direct matches 
      # I.e. x(content) == x(content)
      partialPool = []
      #print("1",statement["stanzaParsed"]["components"][14])
      matches = compareComponentsDirect(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      #print("2",statement["stanzaParsed"]["components"][14])
      matches = compareComponentsWrongSymbol(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      
      #print("3",statement["stanzaParsed"]["components"][14])
      print(matches,"\n")
      print(partialPool)

      statementData = dict()
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
   
   """
   print(len(outData))
   print(outData[0]["partialPool"])
   print("\n\nPartialPool:\n")
   print(type(outData[0]["partialPool"][0]))
   """

   with open(outfilename, "w") as output:
      json.dump(outData, output, indent=2)


def compareComponentsDirect(manual:list, automa:list, 
                            output:np.array, partialPool:list[dict]) -> dict:
   """Directly compares components from manual and automatically annotated statements,
   removes direct matches and adds to a count for the true positive rate of that specific component
   """

   for i in range(17):
      if manual[i] == None or automa[i] == None:
         continue
      #print("I is: ", i)
      #print(manual[i])
      #print(automa[i])
      manualLen = len(manual[i])
      automaLen = len(automa[i])
      j = 0
      k = 0
      while j < manualLen:
         while k < automaLen:
            if manual[i] != None and automa[i] != None:
               #print(type(manual[i]), type(automa[i]))
               if manual[i][j]["Content"] == automa[i][k]["Content"]:
                  if manual[i][j]["Nested"] == automa[i][k]["Nested"]:
                     output[i][0] += 1
                  else:
                     output[i][1] += 1
                  # Add the components to the partialPool
                  entry = {}
                  entry["ManualComponents"] = [manual[i][j]]
                  entry["StanzaComponents"] = [automa[i][k]]
                  partialPool.append(entry)

                  # Remove the components from the list of components
                  automa[i] = automa[i][:k] + automa[i][k+1:]
                  manual[i] = manual[i][:j] + manual[i][j+1:]

                  manualLen -= 1
                  automaLen -= 1
                  #Remove both
                  #print("Match")
            k+=1
         j+=1
   return output

def compareComponentsWrongSymbol(manual:list, automa:list, 
                                 output:np.array, partialPool:list[dict]) -> dict:
   """Directly compares components from manual and automatically annotated statements,
   removes content matches with incorrect symbols and adds to a count for the partial positive 
   rate of that specific component
   """

   for i in range(17):
      for l in range(17):
         if manual[i] == None or automa[l] == None:
            continue
         j = 0
         k = 0
         manualLen = len(manual[i])
         automaLen = len(automa[l])
         while j < manualLen:
            while k < automaLen:
               if manual[i] != None and automa[i] != None:
                  #print(type(manual[i]), type(automa[l]))
                  if manual[i][j]["Content"] == automa[l][k]["Content"]:
                     output[l][1] += 1
                     print("COMPONENT: ", automa[l][k])
                     # Add the components to the partialPool
                     entry = {}
                     entry["ManualComponents"] = [manual[i][j]]
                     entry["StanzaComponents"] = [automa[l][k]]
                     partialPool.append(entry)

                     # Remove the components from the list of components
                     automa[l] = automa[l][:k] + automa[l][k+1:]
                     manual[i] = manual[i][:j] + manual[i][j+1:]
                     manualLen -= 1
                     automaLen -= 1

                     print("Match, partial")
               k+=1
            j+=1

   return output

def combineComponents(input) -> list:
   output = []
   for components in input:
      if components != None and len(components) > 0:
         [output.append(component) for component in components]
   return output


main()