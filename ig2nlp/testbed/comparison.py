import numpy as np

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
                  output[i][1] += 1
                  #print("COMPONENT: ", automa[l][k])

                  # Look for further inclusions on the new substring
                  extraText = manual[i][j]["Content"].replace(automa[l][k]["Content"], "")
                  entry = {}
                  entry["ManualComponents"] = [manual[i][j]]
                  entry["StanzaComponents"] = [automa[l][k]]

                  # Remove the components from the list of components
                  automa[l] = automa[l][:k] + automa[l][k+1:]
                  manual[i] = manual[i][:j] + manual[i][j+1:]

                  entry, output = extraInclusions(automa, output, extraText, entry, False)

                  # Add the components to the partialPool
                  partialPool.append(entry)

                  manualLen = len(manual[i])
                  automaLen = len(automa[l])
                  j-=1
                  break

                  
               elif manual[i][j]["Content"] in automa[l][k]["Content"]:
                  #print(manual[i][j],automa[l][k])
                  #print("Match, substring")
                  output[i][1] += 1
                  #print("COMPONENT: ", automa[l][k])

                  # Look for further inclusions on the new substring
                  extraText = automa[l][k]["Content"].replace(manual[i][j]["Content"], "")
                  entry = {}
                  entry["ManualComponents"] = [manual[i][j]]
                  entry["StanzaComponents"] = [automa[l][k]]

                  # Remove the components from the list of components
                  automa[l] = automa[l][:k] + automa[l][k+1:]
                  manual[i] = manual[i][:j] + manual[i][j+1:]

                  entry, output = extraInclusions(manual, output, extraText, entry, True)

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

def extraInclusions(components:list, output:np.array, extraText:str, 
                    entry:dict, isManual:bool) -> tuple[dict, np.array]:
   """
      Finds extra partial content matches for the remainder of the text of a component in a partial
      match.
   """
   #Remove trailing or prepending space from extraText
   if len(extraText) < 2:
      print(extraText, " too short")
      return entry, output
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