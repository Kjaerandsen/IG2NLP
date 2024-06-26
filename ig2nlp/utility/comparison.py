import json

import numpy as np
import pandas as pd

from utility.componentStatistics import COMPNAMES

def compare(jsonData:dict, outfilename:str) -> None:
   outData:list[dict] = []

   totalMatches = np.zeros((17,5), dtype=int)
   for statement in jsonData:
      matches = np.zeros((17,5), dtype=int)
      #print(statement["name"])
      #print(statement["autoTxParsed"])

      """
      Compare components for direct matches 
      I.e. x(content) == x(content)
      """
      partialMatches = []
      
      #True positive scope and symbol, also accounts for invalid nesting
      matches = compareComponentsDirect(statement["manuTxParsed"]["components"],
                                        statement["autoTxParsed"]["components"],
                                        matches, partialMatches)
      
      # True positive scope, wrong symbol
      matches = compareComponentsWrongSymbol(statement["manuTxParsed"]["components"],
                                        statement["autoTxParsed"]["components"],
                                        matches, partialMatches)
      
      # Partial content matches
      matches = compareComponentsPartial(statement["manuTxParsed"]["components"],
                                        statement["autoTxParsed"]["components"],
                                        matches, partialMatches)
      
      # Count the non-matched components as False Positives from auto, and False Negatives from manu
      matches = countFPandFN(statement["manuTxParsed"]["components"],
                                        statement["autoTxParsed"]["components"],
                                        matches)
      
      partialExtra = dict()
      partialExtra["autoTxComponents"] = []
      partialExtra["manuTxComponents"] = []

      # Count the total amount of matches in each category (TP, PP, FP, FN) for each component type
      matches = countTotal(matches)

      # Add this statements matches to the total
      totalMatches += matches
      statementData = dict()
      
      statementData["Count"] = []
      count = matches.tolist()
      for j in range(17):
         matchData=COMPNAMES[j]+(6-len(COMPNAMES[j]))*" "+": "+str(count[j][0])
         for k in range(4):
            matchData+=","+str(count[j][k+1])
         statementData["Count"].append(matchData)
         
      #statementData["Count"]=matches.tolist()

      for dataPoint in ["name","baseTx","manuTx","autoTx"]:
         statementData[dataPoint] = statement[dataPoint]
      statementData["extraComponents"] = dict()
      # Combine all components to a pool of extra components
      statementData["extraComponents"]["manuTx"] = combineComponents(
         statement["manuTxParsed"]["components"])
      statementData["extraComponents"]["autoTx"] = combineComponents(
         statement["autoTxParsed"]["components"])
      statementData["partialMatches"] = partialMatches
      outData.append(statementData)
   
   #print(matches,"\n")

   # Write all partial matches, extra components and individual statement counts
   with open(outfilename+".json", "w") as output:
      json.dump(outData, output, indent=2)
   
   # Write the totals in each category to a separate total file
   # Create a dataframe (table) of the match statistics
   df = pd.DataFrame(columns=["Symbol", "TP", "PP", "FP", "FN", "Total"])
   """
   COMPNAMES = ["Attribute Property", "Direct Object", "Direct Object Property", "Indirec Object",
                "Indirect Object Property", "Activation Condition", "Execution Contraint",
                "Constituted Entity Property", "Constituting Properties", 
                "Constituting Properties Property", "Or Else", "Attribute", "Deontic", "Aim",
                "Contituted Entity", "Modal", "Constitutive Function"]
   """
   for i in range(17):
      df = df._append({
         "Symbol":COMPNAMES[i], 
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

   df = pd.DataFrame(columns=["Symbol", "TP", "PP", "FP", "FN", "Total"])
   for i in range(17):
      if int(totalMatches[i][4]) != 0:
         df = df._append({
            "Symbol":COMPNAMES[i], 
            "TP":np.round(100*int(totalMatches[i][0])/int(totalMatches[i][4]),2),
            "PP":np.round(100*int(totalMatches[i][1])/int(totalMatches[i][4]),2), 
            "FP":np.round(100*int(totalMatches[i][2])/int(totalMatches[i][4]),2), 
            "FN":np.round(100*int(totalMatches[i][3])/int(totalMatches[i][4]),2), 
            "Total":int(totalMatches[i][4])
         },ignore_index=True)
      else:
         df = df._append({
            "Symbol":COMPNAMES[i], 
            "TP":0,
            "PP":0, 
            "FP":0, 
            "FN":0, 
            "Total":0
         },ignore_index=True)

   df = df.sort_values(by=['Symbol'])

   #print(df)
   # Create totals
   with open(outfilename+"TotalPercentages.txt", "w") as output:
      output.write(str(df))

def compareComponentsDirect(manual:list, automa:list, 
                            output:np.array, partialMatches:list[dict]) -> dict:
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
      while j < manualLen:
         # Reset k, to check against all automatic components for each manual component
         k=0
         while k < automaLen:
            #print(manualLen, j, automaLen, k)
            #print(type(manual[i]), type(automa[i]))
            #print("Comp: ", manual[i][j]["Content"].lower(), automa[i][k]["Content"].lower())
            if manual[i][j]["Content"].lower() == automa[i][k]["Content"].lower():
               if manual[i][j]["Nested"] == automa[i][k]["Nested"]:
                  #print("\n\nDIRECT NESTED EQUAL", automa[i][k], manual[i][j],"\n\n")
                  output[i][0] += 1
               else:
                  output[i][1] += 1
                  #print("\n\nDIRECT NESTED UNEQUAL", automa[i][k], manual[i][j],"\n\n")
                  # Add the components to the partialMatches
                  entry = {}
                  entry["manuTxComponents"] = [manual[i][j]]
                  entry["autoTxComponents"] = [automa[i][k]]
                  partialMatches.append(entry)

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
                                 output:np.array, partialMatches:list[dict]) -> dict:
   """Directly compares components from manual and automatically annotated statements,
   removes content matches with incorrect symbols and adds to a count for the partial positive 
   rate of that specific component
   """

   for i in range(17):
      for l in range(17):
         if manual[i] == None or automa[l] == None:
            continue
         j = 0
         manualLen = len(manual[i])
         automaLen = len(automa[l])
         while j < manualLen:
            # Reset k, to check against all automatic components for each manual component
            k = 0
            while k < automaLen:
               #print(type(manual[i]), type(automa[l]))
               if manual[i][j]["Content"].lower() == automa[l][k]["Content"].lower() \
                  and validateComponentPairMiddleware(manual[i][j]["componentType"], 
                                            automa[l][k]["componentType"]):
                  output[i][1] += 1
                  #print("COMPONENT: ", automa[l][k])
                  # Add the components to the partialMatches
                  entry = {}
                  entry["manuTxComponents"] = [manual[i][j]]
                  entry["autoTxComponents"] = [automa[l][k]]
                  partialMatches.append(entry)

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
                                 output:np.array, partialMatches:list[dict]) -> dict:
   """Directly compares components from manual and automatically annotated statements,
   removes content matches with incorrect symbols and adds to a count for the partial positive 
   rate of that specific component
   """

   for i in range(17):
      for l in range(17):
         if manual[i] == None or automa[l] == None:
            continue
         j = 0
         manualLen = len(manual[i])
         automaLen = len(automa[l])
         while j < manualLen:
            # Reset k, to check against all automatic components for each manual component
            k = 0
            while k < automaLen:
               
               autoMatch = False
               manuMatch = False
               if automa[l][k]["Content"] in manual[i][j]["Content"]:
                  autoMatch = validateComponentPairMiddleware(automa[l][k]["componentType"], 
                                                    manual[i][j]["componentType"])
               elif manual[i][j]["Content"] in automa[l][k]["Content"]:
                  manuMatch = validateComponentPairMiddleware(automa[l][k]["componentType"], 
                                                    manual[i][j]["componentType"])
               componentType = manual[i][j]["componentType"]
                  
               #print(type(manual[i]), type(automa[l]))
               if autoMatch or manuMatch:
                  #print("Match, substring")
                  #print(automa[l][k],manual[i][j])
                  output[i][1] += 1
                  #print("COMPONENT: ", automa[l][k])

                  # Look for further inclusions on the new substring
                  if autoMatch:
                     #print(automa[l][k],manual[i][j])
                     extraText = manual[i][j]["Content"].replace(automa[l][k]["Content"], "")
                  else:
                     #manual[i][j],automa[l][k]
                     extraText = automa[l][k]["Content"].replace(manual[i][j]["Content"], "")
                  entry = {}
                  entry["manuTxComponents"] = [manual[i][j]]
                  entry["autoTxComponents"] = [automa[l][k]]

                  # Remove the components from the list of components
                  automa[l] = automa[l][:k] + automa[l][k+1:]
                  manual[i] = manual[i][:j] + manual[i][j+1:]

                  if autoMatch:
                     entry, output = extraInclusions(
                        automa, output, extraText, 
                        entry, False, componentType)
                  else:
                     entry, output = extraInclusions(
                        manual, output, extraText, 
                        entry, True, componentType)

                  # Add the components to the partialMatches
                  partialMatches.append(entry)

                  manualLen = len(manual[i])
                  automaLen = len(automa[l])
                  j-=1
                  break
                     
               k+=1
            j+=1

   return output

def extraInclusions(components:list, output:np.array, extraText:str, 
                    entry:dict, isManual:bool, componentType:str) -> tuple[dict, np.array]:
   """
      Finds extra partial content matches for the remainder of the text of a component in a partial
      match.
   """

   #print("Looking for extra inclusions with the component text: ", extraText)
   #Remove trailing or prepending space from extraText
   if len(extraText) < 2:
      #print(extraText, " too short")
      return entry, output
   #print(extraText, " handling")
   if extraText[0] == " ":
      extraText = extraText[1:]
   if extraText[len(extraText)-1] == " ":
      extraText = extraText[:len(extraText)-1]

   #print(extraText, " formatted")

   # Go through the component list and look for content matches
   for i in range(17):
      if components[i] == None:
         continue
      j = 0
      compLen = len(components[i])
      while j < compLen:
         if components[i][j]["Content"] in extraText \
            and validateComponentPairMiddleware(componentType, components[i][j]["componentType"]):
            # Add the component to the entry dict
            if isManual:
               entry["manuTxComponents"].append(components[i][j])
               # Add one to the partial positive count
               output[i][1] += 1
               #print("A")
            else:
               entry["autoTxComponents"].append(components[i][j])
               #print("B")

            extraText = extraText.replace(components[i][j]["Content"], "")

            # Remove the component from the component list
            compLen -= 1
            components[i] = components[i][:j] + components[i][j+1:]

            
            #Remove trailing or prepending space from extraText
            if len(extraText) < 2:
               return entry, output
            if extraText[0] == " ":
               extraText = extraText[1:]
            elif extraText[len(extraText)-1] == " ":
               extraText = extraText[:len(extraText)-2]
            j-=1
         j+=1
   return entry, output

def combineComponents(input) -> list:
   output = []
   for components in input:
      if components != None and len(components) > 0:
         [output.append(component) for component in components]
   return output

def countFPandFN(manual:list, automa:list, 
                            output:np.array) -> np.array:
   """Counts extra components and adds manual to False Negative and automa to False Positive counts
   """

   for i in range(17):
      if manual[i] != None:
         output[i][3] += len(manual[i])
      if automa[i] != None:
         output[i][2] += len(automa[i])
   return output

def countTotal(output:np.array) -> np.array:
   """Sums all matches together to a total match count"""
   for i in range(17):
      for j in range(4):
         output[i][4] += output[i][j]

   return output

def validateComponentPairMiddleware(comp1, comp2) -> bool:
   """Middleware for validateComponentPairs, validates pairs of components for partial matches. 
   Used to exclude certain component pair combinations from partial matches."""
   #print("Validating component pair: ", comp1, comp2)
   if not validateComponentPair(comp1, comp2):
      return False
   else:
      return validateComponentPair(comp2, comp1)

def validateComponentPair(comp1, comp2) -> bool:
   """Validates pairs of components for partial matches. 
   Used to exclude certain component pair combinations from partial matches."""
   match comp1:
      case "A":
         if not comp2 in ["A","A,p"]:
            return False
         
      case "A,p":
         if not comp2 in ["A","A,p"]:
            return False
         
      case "E":
         if not comp2 in ["E","E,p"]:
            return False

      case "E,p":
         if not comp2 in ["E","E,p"]:
            return False

      case "I":
         if comp2 != comp1:
            return False
         
      case "F":
         if comp2 != comp1:
            return False

      case "D":
         if comp2 != comp1:
            return False

      case "M":
         if comp2 != comp1:
            return False

   #print("returning true")      
   return True