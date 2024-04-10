import json
import re


COMPNAMES = ["A,p","Bdir","Bdir,p","Bind","Bind,p","Cac",
                "Cex","E,p","P","P,p","O","A","D","I","E","M","F"]

def components(jsonData:dict, outfilename:str) -> None:
   outData:list[dict] = []

   for statement in jsonData:
      #count = np.zeros((17), dtype=int)
      data = {}
      for item in ["name","baseTx","manuTx","autoTx"]:
         data[item] = statement[item]

      #print("Running statement: ", statement["name"])
      # Remove all nested components for the initial testing round
      # TODO: Parametarize this
         
      manuSt = removeSuffixes(data["manuTx"])
      autoSt = removeSuffixes(data["autoTx"])
      #print("Done removing Suffixes", manuSt)

      nesting = False
      if nesting == False:
         manuSt = removeNesting(manuSt)
         autoSt = removeNesting(autoSt)
      #print("Done removing nesting")

      # Remove suffixes:
      manuSt = manuSt.replace("[AND]","and")
      manuSt = manuSt.replace("[OR]","or")
      manuSt = manuSt.replace("[XOR]","or")
      autoSt = autoSt.replace("[AND]","and")
      autoSt = autoSt.replace("[OR]","or")
      autoSt = autoSt.replace("[XOR]","or")

      #print("7", "Manual statement: ", manuSt,"\n", data["manuTx"])

      #print(manuSt)
      #print(autoSt)

      data["manuTxParsed"] = {}
      data["manuTxParsed"]["components"], data["manuTxParsed"]["count"] = \
         getComponents(manuSt)
      data["autoTxParsed"] = {}
      data["autoTxParsed"]["components"], data["autoTxParsed"]["count"] = \
         getComponents(autoSt)

      #"manuTxParsed": {"components":{},"count":[]}
      #"autoTxParsed": {"components":{},"count":[]}
      
      outData.append(data)

   with open(outfilename+".json", "w") as output:
      json.dump(outData, output, indent=2)


def removeNesting(statement:str) -> str:
   """Takes a statement, returns the statement text 
   with all nested component replaced by plain text"""
   output = ""
   # Iterate over the component types
   for comp in [r"A,p[{\[]",r"Bdir[{\[]",r"Bdir,p[{\[]",r"Bind[{\[]",r"Bind,p[{\[]",r"Cac[({\[]",
                r"Cex[{\[]",r"E,p[{\[]",r"P[{\[]",r"P,p[{\[]",r"O[{\[]"]:
      compStatement = statement
      match = re.search(comp,compStatement)
      output = ""
      while match != None:
         # Validate the entry
         # Check if the last symbol is either "{" or "["
         span = match.span()

         # if semantic, find end, validate that the component is nested
         if compStatement[span[1]-1] == "[":
            i = findScopeEnd(span[1], "[","]", compStatement)
            
            if compStatement[i+1] != "{":
               #print("Not nested semantic removeNesting")
               output += compStatement[:i]
               compStatement = compStatement[i:]

               #print("4 Output before nesting re:", output)
               match = re.search(comp,compStatement)
               continue
            else:
               #print("Nested semantic removeNesting")
               spanStart = i+2
               i = findScopeEnd(spanStart, "{","}", compStatement)
               span = (spanStart,i)

               content = formatContent(removeAnnotations(compStatement[span[0]:span[1]]))
               #print("1", compStatement, comp, content)

               output += compStatement[:span[0]]
               output += content
               # Update the statement text to search the rest of the sentence
               
               compStatement = compStatement[span[1]:]

               #print("3 Output before nesting re:", output)
               # Iterate
               match = re.search(comp,compStatement)
               continue
         elif compStatement[span[1]-1] == "{":
            # If nested remove internal annotations
            i = findScopeEnd(span[1], "{","}", compStatement)
            span = (span[1],i)

            content = formatContent(removeAnnotations(compStatement[span[0]:span[1]]))
            #print("2", compStatement, comp, content)

            # check the rest of the sentence
            output += compStatement[:span[0]]
            output += content
            # Update the statement text to search the rest of the sentence
            compStatement = compStatement[span[1]:]

            #print("2 Output before nesting re:", output)
            # Iterate
            match = re.search(comp,compStatement)
         else:
            # Update the statement text to search the rest of the sentence
            output = compStatement[:span[1]]
            compStatement = compStatement[span[1]:]

            #print("1 Output before nesting re:", output)
            # Iterate
            match = re.search(comp,compStatement)
      
      # Update the statement with the new statement text without the suffixes
      statement = output + compStatement

   return statement

def findScopeEnd(position:int, start:str, end:str, text:str) -> int:
   bracketCount = 1
   foundEnd = False

   #print("3", text, "Position: ", text[position], position)

   for i in range(position,len(text)):
      if text[i] == start:
         bracketCount += 1
      elif text[i] == end:
         bracketCount -= 1
      if bracketCount == 0:
         foundEnd = True
         break
   if not foundEnd and bracketCount > 0:
      #print(len(text), i, foundEnd, text[i], start, end)
      #print("4", "Error, could not find end of semantic annotation")
      exit()
   
   #print("5", "Returning i: ", i, '"', text[i], '"', text[position], len(text))
   return i

def removeAnnotations(statement:str) -> str:
   """Takes a statement, or component contents, returns the text with all annotations removed"""
   statement = statement.replace("[AND]","and")
   statement = statement.replace("[OR]","or")
   statement = statement.replace("[XOR]","or")

   output = ""
   for comp in [r"A[({\[]",
                r"A,p[({\[]",
                r"D[({\[]",
                r"I[({\[]",
                r"Bdir[({\[]",
                r"Bdir,p[({\[]",
                r"Bind[({\[]",
                r"Bind,p[({\[]",
                r"Cac[({\[]",
                r"Cex[({\[]",
                r"E,p[({\[]",
                r"P[({\[]",
                r"P,p[({\[]",
                r"O[({\[]",
                r"F[({\[]",
                r"M[({\[]",
                r"E[({\[]"]:
      compStatement = statement
      match = re.search(comp,compStatement)
      output = ""
      #print("6", match, comp)
      while match != None:
         # Validate the entry
         # Check if the last symbol is either "{" or "["
         span = match.span()

         # if semantic, find end, validate that the component is nested
         if compStatement[span[1]-1] == "[":
            #print("Found semantic annotation")
            i = findScopeEnd(span[1], "[","]", compStatement)
            
            # If the component match is a false positive (no encapsulation brackets), iterate
            if compStatement[i+1] != "{" and compStatement[i+1] != "(":
               #print("Could not find subsequent bracket")
               output += compStatement[:span[0]]
               compStatement = compStatement[i:]

               match = re.search(comp,compStatement)
               continue
            else:
               output += compStatement[:span[0]]

               # If nested remove the annotations within the nested structure and iterate
               if compStatement[i+1] == "{":
                  start = "{"
                  end = "}"
                  spanStart = i+2
                  i = findScopeEnd(spanStart, start,end, compStatement)
                  span = (spanStart,i)
                  content = compStatement[span[0]:span[1]]
                  content = removeAnnotations(content)
                  content = formatContent(content)
                  #print(compStatement, comp, content)
               # Else handle the component and iterate
               else:
                  start = "("
                  end = ")"
                  spanStart = i+2
                  i = findScopeEnd(spanStart, start,end, compStatement)
                  span = (spanStart,i)

                  content = formatContent(compStatement[span[0]:span[1]])
                  #print(compStatement, comp, content)
               
               output += content
               # Update the statement text to search the rest of the sentence
               compStatement = compStatement[span[1]+1:]

               # Iterate
               match = re.search(comp,compStatement)
               continue

            #span = (span[0],i)

         if compStatement[span[1]-1] == "(":
            start = "("
            end = ")"
            preComp = span[0]
            # If nested remove internal annotations
            i = findScopeEnd(span[1], start,end, compStatement)
            span = (span[1],i)

            content = formatContent(compStatement[span[0]:span[1]])
         elif compStatement[span[1]-1] == "{":
            start = "{"
            end = "}"
            preComp = span[0]
            # If nested remove internal annotations
            i = findScopeEnd(span[1], start,end, compStatement)
            span = (span[1],i)
            content = compStatement[span[0]:span[1]]
            content = removeAnnotations(content)
            content = formatContent(content)
         else:
            # check the rest of the sentence
            output += compStatement[:span[1]]
            # Update the statement text to search the rest of the sentence
            compStatement = compStatement[span[1]:]

            # Iterate
            match = re.search(comp,compStatement)
            continue
         
         #print(compStatement, comp, content)

         # check the rest of the sentence
         output += compStatement[:preComp]
         output += content
         # Update the statement text to search the rest of the sentence
         compStatement = compStatement[span[1]+1:]

         # Iterate
         match = re.search(comp,compStatement)
      
      # Update the statement with the new statement text without the suffixes
      statement = output + compStatement


   return statement

def removeSuffixes(statement:str) -> str:
   """Takes a statement, returns the statement text with suffixes removed from all components."""
   output = ""
   regStrs = [r"A\d+",r"A,p\d+",r"I\d+",r"Bdir\d+",r"Bdir,p\d+",r"Bind\d+",r"Bind,p\d+",
              r"Cac\d+",r"Cex\d+",r"E\d+",r"E,p\d+",r"P\d+",r"P,p\d+"]
   for comp in regStrs:
      compStatement = statement
      match = re.search(comp,compStatement)
      output = ""
      while match != None:
         # Add the text prepending the component to the output
         output += compStatement[:match.span()[0]]

         # Replace all integer numbers (Suffixes) with empty space
         # the substitution function below was retrieved from the answer by RocketDonkey:
         # https://stackoverflow.com/questions/12851791/removing-numbers-from-string
         contents = ''.join([i for i in match.group() if not i.isdigit()])
         
         # Replace the instance with the symbol without suffixes
         output += contents

         # Update the statement text to search the rest of the sentence
         compStatement = compStatement[match.span()[1]:]

         # Iterate
         match = re.search(comp,compStatement)
      
      # Update the statement with the new statement text without the suffixes
      statement = output + compStatement
   return statement

def getComponents(statement:str) -> tuple[list[dict],list[int]]:
   output = [None] * 17
   count = [0]*17

   regStrs = [r"A,p[({\[]",r"Bdir[({\[]",r"Bdir,p[({\[]",r"Bind[({\[]",r"Bind,p[({\[]",r"Cac[({\[]",
              r"Cex[({\[]",r"E,p[({\[]",r"P[({\[]",r"P,p[({\[]",r"O[({\[]",r"A[({\[]",r"D[({\[]",
              r"I[({\[]",r"E[({\[]",r"M[({\[]",r"F[({\[]"]
   
   for j in range(len(regStrs)):
      #print("GetComponents: ", COMPNAMES[j], "\n", statement)
      comp = regStrs[j]
      compStatement = statement
      match = re.search(comp,compStatement)
      while match != None:
         # Validate the entry
         # Check if the last symbol is either "{" or "["
         span = match.span()

         # if semantic, find end, validate that the component is nested
         if compStatement[span[1]-1] == "[":
            #print("Found semantic annotation")
            i = findScopeEnd(span[1], "[","]", compStatement)
            
            if compStatement[i+1] != "{" and compStatement[i+1] != "(":
               #print("Could not find subsequent bracket")
               output += compStatement[:span[0]]
               compStatement = compStatement[i:]

               match = re.search(comp,compStatement)
               continue
            else:
               if compStatement[i+1] == "{":
                  start = "{"
                  end = "}"
                  nested = True
               else:
                  start = "("
                  end = ")"
                  nested = False

               spanStart = i+2
               i = findScopeEnd(spanStart, start,end, compStatement)
               span = (spanStart,i)

               content = formatContent(compStatement[span[0]:span[1]])
               #print("Component match: ", comp, content, compStatement)
               component = {}
               component["Content"] = content
               component["Nested"] = nested
               component["SemanticAnnotation"] = ""
               component["componentType"] = COMPNAMES[j]
               component["StartID"] = 0

               #print("Appending component")
               if output[j] != None:
                  output[j].append(component)
               else:
                  output[j] = [component]
               count[j] += 1
               #print(output[j])
               # Update the statement text to search the rest of the sentence
               compStatement = compStatement[span[1]:]

               # Iterate
               match = re.search(comp,compStatement)
               continue

            #span = (span[0],i)

         if compStatement[span[1]-1] == "(":
            start = "("
            end = ")"
            nested = False
         elif compStatement[span[1]-1] == "{":
            start = "{"
            end = "}"
            nested = True
         else:
            # check the rest of the sentence
            output += compStatement[:span[1]]
            # Update the statement text to search the rest of the sentence
            compStatement = compStatement[span[1]:]

            # Iterate
            match = re.search(comp,compStatement)
            continue
         
         # If nested remove internal annotations
         i = findScopeEnd(span[1], start,end, compStatement)
         span = (span[1],i)

         content = formatContent(compStatement[span[0]:span[1]])
         
         #print("Component match: ", comp, content, "\n", compStatement)
         #print(content)

         # check the rest of the sentence
         component = {}
         component["Content"] = content
         component["Nested"] = nested
         #component["SemanticAnnotation"] = ""
         component["componentType"] = COMPNAMES[j]
         #component["StartID"] = 0

         #print("Appending component")
         if output[j] != None:
            output[j].append(component)
         else:
            output[j] = [component]
         count[j] += 1
         #print(output[j])

         # Update the statement text to search the rest of the sentence
         compStatement = compStatement[span[1]:]

         # Iterate
         match = re.search(comp,compStatement)

   return output, count
      
def formatContent(content:str) -> str:
   content = content.lower()
   content = content.replace("  ", " ")
   content = content.replace(" and ", " ")
   content = content.replace(" or ", " ")
   content = content.replace(", ", " ")
   content = content.replace("[", "")
   content = content.replace("]", "")
   content = content.replace("(", "")
   content = content.replace(")", "")
   content = content.replace("the ", "")

   return content