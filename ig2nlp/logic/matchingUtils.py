from utility.utility import *
import numpy as np

def smallLogicalOperator(words:wordList, i:int, symbol:str, wordLen:int, root:bool=False) -> int:
   """Finds the scope of components with logical operators and handles the logical operators"""
   scopeStart = i  
   scopeEnd = i

   j=scopeStart+1
   # Locations (ids) of cc dependent words
   ccLocs = []
   # Locations (ids) of puncts
   punctLocs = []
   # Locations (ids) of determiners
   detLocs = []

   if symbol == "I" or symbol == "F":
      # Go through the word list and find the scope of the component
      while j < wordLen:
         if ifHeadRelationRoot(words, j, i):
            scopeEnd, j = LogicalOperatorHelper(words[j], wordLen, scopeEnd, ccLocs, j)
         j += 1
   else:
      while j < wordLen:
         # Go through the word list and find the scope of the component
         if ifHeadRelation(words, j, i):
            scopeEnd, j = LogicalOperatorHelper(words[j], wordLen, scopeEnd, ccLocs, j)
         j += 1
      
   ccCount = len(ccLocs)

   # If the scope is larger than one word in length and there is a cc deprel in the scope (and/or)
   if scopeEnd - scopeStart != 0 and ccCount > 0:
      # Go through the scope, if a deprel other than conj, cc and det is found
      # then handle it as a single word component instead.
      for j in range(scopeStart, scopeEnd):
         if words[j].deprel == "det":
            if j == scopeStart:
               detLocs.append(j)
            elif j-1 >= 0 and words[j-1].deprel == "cc":
               detLocs.append(j)
         # Remove additional puncts (i.e. "x, and y" -> "x and y")
         elif words[j].deprel == "punct" and words[j].text == ",":
            if j+1 < wordLen and words[j+1].deprel == "cc":
               words[j].spaces = 0
               words[j].text = ""
            # If the word is a punct connected to the conj, then it should be replaced by a
                  # logical operator
            elif words.getHeadDep(j) == "conj":
               punctLocs.append(j)

      # Remove dets
      for det in detLocs:
         k = det
         words[k].spaces = 0
         words[k].text = ""

      words[scopeStart].setSymbol(symbol, 1)
      words[scopeEnd].setSymbol(symbol, 2)
      
      i = scopeEnd

      # If there is only one CC in the component
      if ccCount == 1:
         # Set the contents of the cc to be a logical operator
         words[ccLocs[0]].toLogical()

         # Turn all extra punct deprels into the same logical operator as above
         for punct in punctLocs:
            words[punct].spaces += 1
            words[punct].text = words[ccLocs[0]].text

      else:
         # Go through the list of words, create lists of logical operator sequences
         ccLocs2 = []
         ccTypes = []
         orConj = False
         andConj = False

         ccLocs = ccLocs + punctLocs

         for j in range(scopeStart, scopeEnd+1):
            if words[j].text == ",":
               if j+1 in ccLocs:
                  words[j].text = ""
                  if j in punctLocs: punctLocs.remove(j)
               else:
                  currOperatorLoc = next(
                     (i for i, val in enumerate(ccLocs) if val > j), -1)
                  # Set the currOperatorLoc to the value instead of the id
                  currOperatorLoc = ccLocs[currOperatorLoc]
                  if currOperatorLoc != -1:
                     words[currOperatorLoc].toLogical()
                     if words[currOperatorLoc].text == "[AND]":
                        ccLocs2.append(j)
                        ccTypes.append("AND")
                     elif words[currOperatorLoc].text == "[OR]":
                        ccLocs2.append(j)
                        ccTypes.append("OR")
                     else:
                        print("Error, unknown cc")
                        return
                     words[j].text = words[currOperatorLoc].text
                     words[j].spaces = 1
                  else:
                     logger.error(
                        "Error, punct not followed by a logical operator in logical"+
                        " operator handling.")
            elif words[j].deprel == "cc":
               #logger.warning(words[j].text + " " + words[j].deprel)
               if words[j].text.lower() in ["and", "or", "[and]", "[or]"]:
                  words[j].toLogical()
                  if words[j].text == "[AND]":
                     ccLocs2.append(j)
                     ccTypes.append("AND")
                     andConj = True
                  else:
                     ccLocs2.append(j)
                     ccTypes.append("OR")
                     orConj = True
               # TODO: potentially remove "as" (as well as) as a logical operator match for "and"
               elif words[j].text.lower() == "as":
                  words[j].text = "[AND] " + words[j].text
                  ccLocs2.append(j)
                  ccTypes.append("AND")
                  andConj = True

         originalType = ccTypes[0]
         prevOperator = ccTypes[0]
         prevOperatorLoc = ccLocs2[0]
         # If there is a mix and match between symbol types handle the bracketing
         if andConj and orConj:
            logger.warning('Found both "and" and "or" logical operators in component, '+
                  "please review manually to solve potential encapsulation issues.")

            # Go through all the cc and handle the bracketing
            for nextLoc, nextType in zip(ccLocs2, ccTypes):
               if prevOperator == originalType:
                  # If next operator is not then add the first word after the operator
                  # as the starting bracket
                  if nextType != originalType:
                     words[prevOperatorLoc+1].text = "(" + words[prevOperatorLoc+1].text
               else:
                  # If previous is not original and this is then close the bracket
                  if nextType == originalType:
                     words[nextLoc-1].text += ")"
               # Update the previous operator
               prevOperator = nextType
               prevOperatorLoc = nextLoc

         # If the last operator is not the original add a closing bracket
         if ccTypes[len(ccLocs2)-1] != originalType:
            words[scopeEnd].text += ")"
         
         logger.warning("More than one CC in smallLogicalOperator function, " +
                      "please review logical operators")
         
      return scopeEnd
   
   else:
      words[i].setSymbol(symbol)
      return i
   
def includeConj(words:wordList, i:int, wordLen:int) -> int:
   """Function for including logical operators in symbols without handling (annotating) them"""
   symbol = words[i].symbol
   scopeEnd = i

   j = i
   if symbol == "I" or symbol == "F":
      # Go through the word list and find the scope of the component
      while j < wordLen:
         if ifHeadRelationRoot(words, j, i):
            scopeEnd, j = LogicalOperatorHelper(words[j], wordLen, scopeEnd, [], j)
         j += 1
   else:
      while j < wordLen:
         # Go through the word list and find the scope of the component
         if ifHeadRelation(words, j, i):
            scopeEnd, j = LogicalOperatorHelper(words[j], wordLen, scopeEnd, [], j)
         j += 1

   if scopeEnd != i and scopeEnd < wordLen:
      words[scopeEnd].setSymbol(words[i].symbol,2)
      words[i].setSymbol()

   return scopeEnd

def LogicalOperatorHelper(word:Word, wordLen:int, scopeEnd:int, 
                    ccLocs:list[int], j:int) -> tuple[int, int]:
   """Adds cc deprels to ccLocs and escapes the sequence if
      an unsupported deprel is detected"""
   supported = ["punct","det","advmod","amod"]

   if word.deprel == "cc":
      # TODO: potentially remove "as" (as well as) as a logical operator match for "and"
      if word.text.lower() in ["and","or","as"]:
         ccLocs.append(j)
         scopeEnd = j
   elif word.deprel == "conj":
      scopeEnd = j
   # Also include advmod dependencies
   elif word.deprel == "advmod":
      scopeEnd = j
   # If the word is anything else than the supported components 
   # break the loop to not include further components
   elif not word.deprel in supported:
      j=wordLen-1
   
   return scopeEnd, j

def validateNested(words:wordList, constitutive:bool) -> bool:
   """Sets a requirement of both an Aim (I) and an Attribute (A) detected for a component to
      be regarded as nested."""
   Activity = False
   Entity = False

   if constitutive:
      entitySymbol = "E"
      activitySymbol = "F"
   else:
      entitySymbol = "A"
      activitySymbol = "I"

   for word in words:
      if word.symbol == entitySymbol:
         Entity = True
         if Activity:
            return True
      if word.symbol == activitySymbol:
         Activity = True
         if Entity:
            return True
   
   return False

def ifHeadRelation(words:wordList, wordId:int, headId:int) -> bool:
   """Check if the word is connected to the headId through a head connection"""
   word = words[wordId]
   # array of visited id's to prevent infinite recursion
   visited = np.array(words[word.head])

   while words[word.head].deprel != "root":
      # If the head is already visited then return False
      if word.head in visited:
         return False
      else:
         # Add the new head to visited
         visited = np.append(visited, word.head)

      if word.deprel == "root":
         return False
      if word.head == headId:
         return True
      # Go to the head of the current word and iterate
      word = words[word.head]
   return False

# List of allowed head connections for the function below
allowedRootHeads = ["conj","cc","det","amod","advmod"]

def ifHeadRelationRoot(words:wordList, wordId:int, headId:int) -> bool:
   """Check if the word is connected to the headId through a head connection, 
   specifically for components detected by the root deprel (Constituted Function (F) and Aim (I))"""
   word = words[wordId]
   # array of visited id's to prevent infinite recursion
   visited = np.array(words[word.head])

   while words[word.head].deprel != "root":
      # If the head is already visited then return False
      if word.head in visited:
         return False
      else:
         # Add the new head to visited
         visited = np.append(visited, word)

      if word.head == headId:
         return True
      if not words[word.head].deprel in allowedRootHeads:
         return False
      word = words[word.head]
   # Exception for the case where the headId is the root
   if words[headId].deprel == "root":
      return True
   return False

def corefReplace(words:wordList, semanticAnnotations:bool) -> wordList:
   """Handles supplementing pronouns with their respective Attribute (A) component contents using
      coreference resolution data"""
   #print("INITIALIZING COREF CHAIN FINDING:\n\n ")
   i = 0
   wordLen = len(words)
   
   corefIds:dict = {}
   locations:dict = {}
   corefStrings:dict = {}

   brackets = 0

   # Get all instances of a coref with the given id
   # if the length of the word is longer than another instance replace the coref string for that
   # coref with the new word
   while i < wordLen:
      if words[i].symbol == "A":
         if words[i].position != 2 and words[i].corefid != -1:
            if words[i].corefid in corefIds:
               corefIds[words[i].corefid] += 1
               locations[words[i].corefid].append(i)
            else:
               corefIds[words[i].corefid] = 1
               locations[words[i].corefid] = [i]

            if words[i].position == 0:
               if words[i].pos != "PRON":
                  if words[i].corefid in corefStrings:
                     if len(corefStrings[words[i].corefid]) < len(words[i].text):
                        corefStrings[words[i].corefid]=words[i].text
                  else:
                     corefStrings[words[i].corefid]=words[i].text
            else:
               iBak = i
               while words[i].position != 2:
                  i+=1
               if words[i].pos != "PRON":
                  if words[i].corefid in corefStrings:
                     if (len(corefStrings[words[i].corefid]) < 
                        len(WordsToSentence(words[iBak:i+1], True))):
                        corefStrings[words[i].corefid]=WordsToSentence(words[iBak:i+1], True)
                  else:
                     corefStrings[words[i].corefid]=WordsToSentence(words[iBak:i+1], True)
      elif (words[i].symbol == "" and words[i].corefid != -1 
           and words[i].pos == "PRON" and not "PronType=Rel" in words[i].feats and brackets == 0):
         if words[i].corefid in corefIds:
            corefIds[words[i].corefid] += 1
            locations[words[i].corefid].append(i)
         else:
            corefIds[words[i].corefid] = 1
            locations[words[i].corefid] = [i]
      else:
         if words[i].position == 1 and words[i].nested == False:
            brackets+=1
         if words[i].position == 2 and words[i].nested == False:
            brackets-=1
      i += 1

   '''
      if words[i].coref[corefLen-2:] == "'s":
         words[i].text = words[:corefLen-2]
      if ":poss" in words[i].deprel:
         words[i].coref += "'s"
   '''

   #print(str(corefIds), str(corefStrings), str(locations))
      
   for key, val in corefIds.items():
      #print(key,val, wordLen)
      for id in locations[key]:
         if words[id].pos == "PRON" and key in corefStrings:
            logger.info("Replacing Attribute (A) pronoun with coreference resolution data: " 
                     + words[id].text + " -> " + corefStrings[key])
            
            words = addWord(words, id, words[id].text)
            words[id+1].text = "["+corefStrings[key]+"]"
            words[id+1].spaces = 1
            words[id+1].setSymbol("A")
            if val > 1 and semanticAnnotations:
               words[id+1].addSemantic("Entity="+corefStrings[key])
      if val > 1 and semanticAnnotations:
         #print("val over 1")
         for id in locations[key]:
            #print(id, "adding entity semanticannotation")
            if key in corefStrings:
               words[id].addSemantic("Entity="+corefStrings[key])
   
   return words

def findInternalLogicalOperators(words:wordList, start:int, end:int) -> wordList:
   """Detects logical operator words, formats them, and replaces preceeding commas with the same
      logical operator"""
   #print("Finding logical operators\n", start, end)
   andCount = 0
   orCount = 0
   for j in range(start, end):
      if words[j].deprel == "cc":
         if words[j].text.lower() in ["and", "or"]:
            words[j].toLogical()
            if words[j].text == "[AND]":
               andCount += 1
            else:
               orCount += 1
            # Remove preceeding puncts
            if j-1 >= 0 and words[j-1].text == ",":
               words[j-1].text = ""
         # TODO: potentially remove "as" (as well as) as a logical operator match for "and"
         elif words[j].text.lower() == "as":
            words[j].text = "[AND] " + words[j].text
            andCount += 1
            # Remove preceeding puncts
            if j-1 >= 0 and words[j-1].text == ",":
               words[j-1].text = ""
         
         #print("CC", words[j])
      #else:
      #   print(words[j].text)
   
   # Internal scoping test
   '''
   j = start
   while j < end:
      if j-1 >= 0 and words[j].deprel == "conj" and words[j-1].deprel == "cc":
         head = words[j].head
         if (words[words[j].head-1].deprel in ["amod", "advmod"] and 
             words[words[j].head-1].head == words[j].head):
            words[head-1].text = "(" + words[head-1].text
         else:
            words[head].text = "(" + words[head].text
         # Positive lookahead for nmod
         foundNmod = False
         for k in range(j+1, len(words)):
            if words[k].head == head and words[k].deprel == "nmod":
               words[k].text += ")"
               foundNmod = True
               j = k
               break
         
         if not foundNmod:
            words[j].text += ")"
      j += 1
   '''
      
   if andCount > 0 and orCount > 0:
      logger.warning('Found both "and" and "or" logical operators in component, '+
                  "please review manually to solve encapsulation issues.")
      # Basic internal scoping, if both [AND] and [OR] are present then encapsulate [OR]
      # TODO: Handle a [AND] b [OR] c [OR] d (encapsulate (b [OR] c [OR] d) not (b [OR] (c) [OR] d))
      # Potentially best to just note all [OR] locs and cc locs, if ccLocs i+1 is not in or locs 
      # close, else just iterate
      for j in range(start,end):
         if j+1 < end and words[j+1].text == "[OR]":
            words[j].text = "(" + words[j].text
         elif j-1 >= start and words[j-1].text == "[OR]":
            words[j].text += ")"

   return words

def attributeSemantic(words:wordList) -> wordList:
   """Adds Number=x semantic annotation to attribute components in a list of words"""
   for word in words:
      if word.symbol == "A":
         if "Number=Sing" in word.feats:
            word.addSemantic("Number=Sing")
         if "Number=Plur" in word.feats:
            word.addSemantic("Number=Plur")

   return words

def logicalOperatorImbalanced(words:wordList) -> None:
   wordLen = len(words)
   for i in range(1, wordLen):
      # If a logical operator is the start and or end of a component 
      # remove the logical operator from the component
      if words[i].text in ["[AND]", "[OR]"] and words[i].symbol != "":
         words[i].text = words[i].text[1:len(words[i].text)-1].lower()
         if i+1 < wordLen and words[i].position == 1:
            if words[i+1].position != 2:
               words[i+1].setSymbol(words[i].symbol,1)
            else: words[i+1].position == 2
         elif words[i].position == 2:
            if i-1 >= 0 and words[i-1].position != 1:
               words[i-1].setSymbol(words[i].symbol,2)
            elif i-1 >= 0: words[i-1].position == 0
         # Remove the old annotation of the logical operator
         words[i].setSymbol()

def handleScopingIssues(words:wordList) -> None:
   """Handler to fix scoping issues causing parsing errors"""
   wordLen = len(words)
   within = False
   start = 0
   i = 0
   while i < wordLen:
      #print("i:", words[i].text, words[i].symbol, words[i].position, words[i].nested)
      if words[i].position == 1 and words[i].nested == False:
         if not within:
            #print("NOT WITHIN")
            within = True
            start = i
         else:
            #print("WITHIN")
            remove = False
            # Look for closing bracket
            if i+1 < wordLen:
               for j in range(i+1, wordLen):
                  if words[j].symbol == words[start].symbol and words[start].nested == False:
                     #print("j: ", words[j].text, words[j].symbol, words[j].position, words[j].nested)
                     if words[j].position == 0 or 2:
                        words[j].position = 2
                        remove = True
                        within = False
                        #print("FOUND END")
                        break
                     else:
                        #print("Removing annotation start: ", words[j].symbol, words[j].position)
                        words[j].setSymbol()
            # If found then remove all internal operators
            if remove:
               for k in range(start+1, j-1):
                  #print("Removing annotation: ", words[j].symbol, words[j].position)
                  words[k].setSymbol()
               i = j
            else:
               #print("Setting start to 0")
               words[start].position = 0
               within = False
      if words[i].position == 2 and words[i].nested == False:
         #print("POSITION 2")
         if within:
            if words[i].symbol == words[start].symbol:
               within = False
      i += 1

def findComponentEnd(words:wordList, id:int, symbol:str) -> int:
   """Function for a positive lookahead to find the end index of a component"""
   for i in range(id+1,len(words)):
      word = words[i]
      if word.symbol == symbol:
         if word.position == 2:
            return id
         else:
            logger.warning("findComponentEnd invalid object scope")
            return -1
      elif word.symbol != "":
         logger.warning("findComponentEnd invalid object scope")
         return -1
   logger.warning("findComponentEnd could not find the end")
   return -1

def findComponentStart(words:wordList, id:int, symbol:str) -> int:
   """Function for a positive lookbehind to find the start index of a component"""
   for i in range(id-1,-1,-1):
      word = words[i]
      if word.symbol == symbol:
         if word.position == 1:
            return id
         else:
            logger.warning("findComponentStart invalid object scope")
            return -1
      elif word.symbol != "":
         logger.warning("findComponentStart invalid object scope")
         return -1
   logger.warning("findComponentStart could not find the start")
   return -1