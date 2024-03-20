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
      
      #True positive scope and symbol, also accounts for invalid nesting
      matches = compareComponentsDirect(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      #print("2",statement["stanzaParsed"]["components"][14])
      # True positive scope, wrong symbol
      matches = compareComponentsWrongSymbol(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      # Partial content matches
      matches = compareComponentsPartial(statement["manualParsed"]["components"],
                                        statement["stanzaParsed"]["components"],
                                        matches, partialPool)
      
      #print("3",statement["stanzaParsed"]["components"][14])
      #print(matches,"\n")
      #print(partialPool)

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
   print(matches,"\n")


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
            #print(manualLen, j, automaLen, k)
            #print(type(manual[i]), type(automa[i]))
            if manual[i][j]["Content"].lower() == automa[i][k]["Content"].lower():
               if manual[i][j]["Nested"] == automa[i][k]["Nested"]:
                  #print("\n\nDIRECT NESTED EQUAL", automa[i][k], manual[i][j],"\n\n")
                  output[i][0] += 1
               else:
                  output[i][1] += 1
                  #print("\n\nDIRECT NESTED UNEQUAL", automa[i][k], manual[i][j],"\n\n")
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
               j -= 1
               break
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
               #print(type(manual[i]), type(automa[l]))
               if manual[i][j]["Content"].lower() == automa[l][k]["Content"].lower():
                  output[l][1] += 1
                  #print("COMPONENT: ", automa[l][k])
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
                  j -= 1
                  #print("Match, partial")
                  break
               k+=1
            j+=1

   return output

def compareComponentsPartial(manual:list, automa:list, 
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
               #print(type(manual[i]), type(automa[l]))
               if automa[l][k]["Content"] in manual[i][j]["Content"]:
                  #print("Match, substring")
                  #print(automa[l][k],manual[i][j])
                  output[l][1] += 1
                  #print("COMPONENT: ", automa[l][k])

                  # Look for further inclusions on the new substring
                  extraText = manual[i][j]["Content"].replace(automa[l][k]["Content"], "")
                  entry = {}
                  entry["ManualComponents"] = [manual[i][j]]
                  entry["StanzaComponents"] = [automa[l][k]]

                  # Remove the components from the list of components
                  automa[l] = automa[l][:k] + automa[l][k+1:]
                  manual[i] = manual[i][:j] + manual[i][j+1:]

                  entry = extraInclusions(automa, output, extraText, entry, False)

                  # Add the components to the partialPool
                  partialPool.append(entry)

                  manualLen = len(manual[i])
                  automaLen = len(automa[l])
                  j-=1
                  break

                  
               elif manual[i][j]["Content"] in automa[l][k]["Content"]:
                  #print(manual[i][j],automa[l][k])
                  #print("Match, substring")
                  output[l][1] += 1
                  #print("COMPONENT: ", automa[l][k])

                  # Look for further inclusions on the new substring
                  extraText = automa[l][k]["Content"].replace(manual[i][j]["Content"], "")
                  entry = {}
                  entry["ManualComponents"] = [manual[i][j]]
                  entry["StanzaComponents"] = [automa[l][k]]

                  # Remove the components from the list of components
                  automa[l] = automa[l][:k] + automa[l][k+1:]
                  manual[i] = manual[i][:j] + manual[i][j+1:]

                  entry = extraInclusions(manual, output, extraText, entry, True)

                  # Add the components to the partialPool
                  partialPool.append(entry)

                  manualLen = len(manual[i])
                  automaLen = len(automa[l])
                  # Iterate
                  j-=1
                  break
                     
               k+=1
            j+=1

   return output

def extraInclusions(components:list, 
                    output:np.array, extraText:str, entry:dict, isManual:bool) -> dict:
   #Remove trailing or prepending space from extraText
   if len(extraText) < 2:
      print(extraText, " too short")
      return entry
   print(extraText, " handling")
   if extraText[0] == " ":
      extraText = extraText[1:]
   elif extraText[len(extraText)-1] == " ":
      extraText = extraText[:len(extraText)-2]

   # Go through the component list and look for content matches
   for i in range(17):
         if components[i] == None:
            continue
         j = 0
         compLen = len(components[i])
         while j < compLen:
            if components[i][j]["Content"] in extraText:
               # Add the component to the entry dict
               if isManual:
                  entry["ManualComponents"].append(components[i][j])
                  print("A")
               else:
                  entry["StanzaComponents"].append(components[i][j])
                  print("B")

               extraText = extraText.replace(components[i][j]["Content"], "")

               # Remove the component from the component list
               compLen -= 1
               components[i] = components[i][:j] + components[i][j+1:]

               
               #Remove trailing or prepending space from extraText
               if len(extraText) < 2:
                  return entry
               if extraText[0] == " ":
                  extraText = extraText[1:]
               elif extraText[len(extraText)-1] == " ":
                  extraText = extraText[:len(extraText)-2]
               j-=1
            j+=1
   return entry

def combineComponents(input) -> list:
   output = []
   for components in input:
      if components != None and len(components) > 0:
         [output.append(component) for component in components]
   return output


main()