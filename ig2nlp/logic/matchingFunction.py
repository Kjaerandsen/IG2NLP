import time
import copy
from utility.utility import *
from logic.matchingUtils import *
import logic.matchingFunctionConstitutive as mc
from logic.classifier import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1
numberAnnotation = False
coref = True

def matchingHandler(words:wordList, semantic:bool) -> wordList:
   """takes a list of words, performs annotations using the matching function and returns 
   a formatted string of annotated text"""
   words = compoundWordsHandler(words)
   words = matchingFunction(words, semantic)
   if coref: words = corefReplace(words, semantic)
   if semantic and numberAnnotation: words = attributeSemantic(words)
   # Handle cases where a logical operator is included in a component without a matching word
   logicalOperatorImbalanced(words)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   handleScopingIssues(words)
   print("Regulative coverage: ", coverage(words))
   return WordsToSentence(words)

def matchingFunction(words:wordList, semantic:bool) -> wordList:
   """takes a list of words with dependency parse and pos-tag data.
      Returns a list of words with IG Script notation symbols."""
   words = wordList(words)
   wordLen = len(words)
   wordsBak = copy.deepcopy(words)
   words2 = wordList()

   # Look for conditions only first, if enabled remove the advcl case from the matching below
   #for i, word in enumerate(words):
   #   if word.deprel == "advcl":
   #      if conditionHandler(words, wordsBak, i, wordLen, words2, False, True):
   #         return words2

   i = 0

   while i < wordLen:
      #print(words[i].text, words[i].symbol, words[i].position)
      word = words[i]
      deprel = word.deprel

      #print(words.getHead(i), words[i].deprel, words[i].text)

      match deprel:
         # (Cac, Cex) Condition detection 
         case "advcl":
            if conditionHandler(words, wordsBak, i, wordLen, words2, semantic):
               return words2
            else:
               i = conditionHandler2(words, i, wordLen)
         
         # (Bdir) Object detection
         case "obj":
            i = bdirHandler(words, i, wordLen)

         # (Bind) Indirect object detection
         case "iobj":
            i = bindHandler(words, i, wordLen)

         # (I) Aim detection
         case "root":
            i = rootHandler(words, i, wordLen)

         # Else if the word has an amod dependency type, check if the head is a symbol
         # that supports properties, if so, the word is a property of that symbol
         # (Bdir,p, Bind,p, A,p)   
         case "amod":
            i = amodPropertyHandler(words, i, wordLen)
            # If the relation is a ccomp then handle it as a direct object
            # This does nothing in testing
            '''
            elif (words[word.head].deprel == "nsubj" 
               and words[words[word.head].head].deprel == "ccomp"):
               #print("\n\nAMOD NSUBJ OBJ\n\n")
               word.setSymbol(word,"bdir", 1)
               words[i+1].setSymbol(words[i+1],"bdir", 2)
               i += 1
            '''
         case "acl":
            # (A,p) Attribute property detection 2
            if words[word.head].symbol == "A":
               word.setSymbol("A,p")
            # (Bdir,p) Direct object property detection 3
            # TODO: Reconsider in the future if this is accurate enough
            # There are currently false positives, but they should be mitigated by better
            # Cex component detection
            if i-1 >= 0 and words.getHeadSymbol(i) == "Bdir" and words[i-1].symbol == "Bdir":
               word.setSymbol("Bdir,p")

         # Direct object handling (Bdir), (Bdir,p)
         case "nmod":
            i = nmodDependencyHandler(words, i, wordLen)
            # TODO: Revisit and test
            #else if words[word.head].symbol == "A":
            #   print("\nnmod connected to Attribute(A): ", word)

         # (Bdir,p) Direct object property detection 2
         case "nmod:poss":
            if words.getHeadDep(i) == "obj" and word.head == i+1:
               # Check if there is a previous amod connection and add both
               if i-1 >= 0 and words[i-1].deprel == "amod" and words[i-1].head == i:
                  words[i-1].setSymbol("Bdir,p", 1)
                  word.setSymbol("Bdir,p", 2)
               # Else only add the Bdir,p
               else:
                  word.setSymbol("Bdir,p")
            #else:
               #print("\nWord is nmod:poss: ", word)
         
         # (O) Or else detection
         case "cc":
            if i+1 < wordLen and words[i+1].text == "else":
               orElseHandler(words, wordsBak, wordLen, words2, i, semantic)
               return words2
         # Advmod of Aim is correlated with execution constraints (Cex)
         # Might be too generic of a rule.
         # TODO: Revisit and test
         case "advmod":
            if words.getHeadSymbol(i) == "I":
               #print("\nadvmod connected to Aim(I): ", word)
               if i+1 < wordLen:
                  if words[i+1].deprel == "punct":
                     word.setSymbol("Cex")
         
         # (Cex) Execution constraint detection
         case "obl":
            i = oblHandler(words, i, wordLen, semantic)
         case "obl:tmod":
            # Old implementation used
            # i = words[i].head
            i = oblHandler(words, i, wordLen, semantic)

         # Default, for matches based on more than just a single deprel
         case _:
            # Print out more complex dependencies for future handling
            #if ":" in deprel:
            #   if deprel != "aux:pass" and deprel != "obl:tmod":
            #      print("\n", '":" dependency: ',words[i], "\n")
            
            # (A) Attribute detection
            # TODO: Consider specyfing which nsubj dependencies specifically to include
            if "nsubj" in deprel:
               i = attributeHandler(words, i, wordLen)

               # TODO: look into the line below
               if words.getHeadDep(i) == "ccomp":
                  logger.debug("NSUBJ CCOMP OBJ")

            # (D) Deontic detection
            elif words.getHeadDep(i) == "root" and "aux" in deprel:
               i = deonticHandler(words, i)

            elif (deprel != "punct" and deprel != "conj" and deprel != "cc"
                 and deprel != "det" and deprel != "case"):
               logger.debug("Unhandled dependency: " + deprel)
      
      #print(words[i].text, words[i].symbol, words[i].position)
      # Iterate to the next word
      #print(WordsToSentence(words))
      i += 1

   return words

def conditionHandler(words:wordList, wordsBak:wordList, i:int, 
                     wordLen:int, words2:wordList, semantic:bool, 
                     constitutive:bool=False, parseFirst:bool=False) -> bool:
   """Handler function for the matching and encapsulation of conditions (Cac, Cex)"""
   firstVal = i

   # TODO: Reconsider the commented out section in favor of the one below
   # The solution below is only effective in cases where there are overlapping activation conditions
   # It may be better to compound these instead.
   """
   # Go through the statement until the word is connected to the advcl directly or indirectly
   for j in range(i):
      # If connected to the advcl then set firstVal to the id and break the loop
      if ifHeadRelation(words, j, i):
         firstVal = j
         break
   """
         
   # Update to check if there are any overlapping annotations
   # Go through the statement until the word is connected to the advcl directly or indirectly
   inComp = False
   nullified = True
   for j in range(i):
      # If connected to the advcl then set firstVal to the id and break the loop
      if ifHeadRelation(words, j, i):
         if inComp and words[j].position == 2:
            inComp = False
         elif words[j].symbol == "Cac":
            inComp = True
            nullified = True
            firstVal = -1
         elif nullified:
            firstVal = j
            nullified = False
   
   if firstVal == -1:
      firstVal = i

   # Go through again from the activation condition++
   # Until the word is no longer connected to the advcl
      
   # Set the lastVal to the current id -1   
   lastIndex = i+1 if i+1 < wordLen else i
   for j in range(lastIndex,wordLen):
      if not ifHeadRelation(words, j, i):
         lastIndex = j-1
         break

   if words[lastIndex].deprel != "punct":
      if words[lastIndex+1].deprel == "punct":
         lastIndex += 1
      else:
         logger.debug("Last val in handleCondition was not punct: " + words[lastIndex].text)
         return False
      
   #print(words[firstVal].text, words[lastIndex].text)

   date = False
   law = False
   if firstVal == 0:
      contents = []

      if constitutive:
         condition = mc.matchingFunctionConstitutive(
            reusePartSoS(copy.deepcopy(wordsBak[:lastIndex]), lastIndex), semantic)
      else:
         condition = matchingFunction(reusePartSoS(copy.deepcopy(wordsBak[:lastIndex]), lastIndex), 
                                      semantic)

      oblCount = 0
      for conditionWord in condition:
         if "obl" in conditionWord.deprel:
            oblCount+=1
         if "DATE" in conditionWord.ner:
            date = True
         if "LAW" in conditionWord.ner:
            law = True

      if oblCount > 1 and words[0].deprel == "mark":
         symbol = "Cex"
      else:
         symbol = "Cac"
         date = False

      if validateNested(condition, constitutive):
         words2.append(Word(
         "","","",0,0,"","","",0,0,0,symbol,True,1
         ))
         if semantic:
            if date:
               words2[len(words2)-1].addSemantic("ctx:tmp")
            if law:
               words2[len(words2)-1].addSemantic("act:law")
         condition[0].spaces = 0
         words2 += condition
         words2.append(Word("","","",0,0,"","","",0,0,0,symbol,True,2))
         words2.append(words[lastIndex])
      else:
         words2 += wordsBak[:lastIndex]
         words2[0].setSymbol(symbol,1)
         if semantic:
            if date:
               words2[0].addSemantic("ctx:tmp") 
            if law:
               words2[0].addSemantic("act:law") 
         words2[lastIndex-1].setSymbol(symbol,2)
         words2.append(words[lastIndex])
         if lastIndex - firstVal > 2:
            words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)

      if constitutive:
         contents = mc.matchingFunctionConstitutive(
            reusePartEoS(words[lastIndex+1:], lastIndex+1), semantic)
      else:
         contents = matchingFunction(
            reusePartEoS(words[lastIndex+1:], lastIndex+1), semantic)

      # Copy over the old placement information to the 
      # newly generated words for proper formatting
      for j in range(lastIndex+1, wordLen):
         index = j-lastIndex-1
         contents[index].id = words[j].id
         contents[index].start = words[j].start
         contents[index].end = words[j].end
         contents[index].spaces = words[j].spaces

      words2 += contents

      return True
   #else:
   elif words[firstVal].deprel == "mark" or words[firstVal].text == ",":
      if words[firstVal].text == ",":
         firstVal+=1
      #print("First val was not id 0 and deprel was mark", words[lastIndex])
      # Do the same as above, but also with the words before this advcl
      contents = []

      # Add the values before the condition
      if parseFirst:
         if constitutive:
            words2 += mc.matchingFunctionConstitutive(reusePartSoS(words[:firstVal], firstVal),
                                            semantic)
         else:
            words2 += matchingFunction(reusePartSoS(words[:firstVal], firstVal), semantic)
      else:
         words2 += words[:firstVal]
      if constitutive:
         condition = mc.matchingFunctionConstitutive(
               reusePartMoS(copy.deepcopy(wordsBak[firstVal:lastIndex]), firstVal, lastIndex),
               semantic)
      else:
         condition = matchingFunction(
               reusePartMoS(copy.deepcopy(wordsBak[firstVal:lastIndex]), firstVal, lastIndex),
               semantic)

      j = 0
      oblCount = 0
      for conditionWord in condition:
         if "obl" in conditionWord.deprel:
            oblCount+=1
         if "DATE" in conditionWord.ner:
            date = True
         if "LAW" in conditionWord.ner:
            law = True

      if oblCount > 1:
         symbol = "Cex"
      else:
         symbol = "Cac"
         date = False

      if validateNested(condition, constitutive):
         words2.append(Word(
         "","","",0,0,"","","",0,0,1,symbol,True,1
         ))
         if semantic:
            if date:
               words2[len(words2)-1].addSemantic("ctx:tmp") 
            if law:
               words2[len(words2)-1].addSemantic("act:law") 
         condition[0].spaces = 0
         words2 += condition
         words2.append(Word("","","",0,0,"","","",0,0,0,symbol,True,2))
         words2.append(words[lastIndex])
      else:
         words2 += wordsBak[firstVal:lastIndex]
         words2[firstVal].setSymbol(symbol,1)
         if semantic:
            if date:
               words2[firstVal].addSemantic("ctx:tmp") 
            if law:
               words2[firstVal].addSemantic("act:law") 
         words2[lastIndex-1].setSymbol(symbol,2)
         words2.append(words[lastIndex])
         if lastIndex - firstVal > 2:
            words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)
      
      if wordLen > lastIndex+1:
         lastPunct = False
         lastVal = wordLen
         if wordsBak[wordLen-1].deprel == "punct":
            lastPunct = True
            lastVal = wordLen-1
            wordLen -= 1
         
         if constitutive:
            contents = mc.matchingFunctionConstitutive(
               reusePartEoS(wordsBak[lastIndex+1:lastVal], lastIndex+1), semantic
            )   
         else:
            contents = matchingFunction(
               reusePartEoS(wordsBak[lastIndex+1:lastVal], lastIndex+1), semantic
            )   

         # Copy over the old placement information to the 
         # newly generated words for proper formatting
         for j in range(lastIndex+1, wordLen):
            index = j-lastIndex-1
            contents[index].id = words[j].id
            contents[index].start = words[j].start
            contents[index].end = words[j].end
            contents[index].spaces = words[j].spaces

         words2 += contents
         if lastPunct:
            words2.append(wordsBak[lastVal])

      return True
   else:
      """
      words[firstVal].setSymbol("Cac",1)
      if words[lastIndex].text in [",","."]:
         lastIndex -= 1
      words[lastIndex].setSymbol("Cac",2)
      words2 += words[:lastIndex+1]
      if lastIndex - firstVal > 2:
         words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)

      if wordLen > lastIndex+1:
         lastPunct = False
         lastVal = wordLen
         if wordsBak[wordLen-1].deprel == "punct":
            lastPunct = True
            lastVal = wordLen-1
            wordLen -= 1
         
         words2.append(wordsBak[lastIndex+1])
         if constitutive:
            contents = mc.matchingFunctionConstitutive(
               reusePartEoS(wordsBak[lastIndex+2:lastVal], lastIndex+1), semantic
            )   
         else:
            contents = matchingFunction(
               reusePartEoS(wordsBak[lastIndex+2:lastVal], lastIndex+1), semantic
            )   

         words2 += contents
         if lastPunct:
            words2.append(wordsBak[lastVal])
         
         print(words2)
      else:
         words2 += words[lastIndex+1:]
      """
      """
      logger.debug("Unhandled advcl: " + words[firstVal].text + " | " + words[firstVal].deprel + 
                  " | " + words[firstVal-1].text + " | " + words[firstVal-1].deprel  )
      logger.debug(WordsToSentence(words[firstVal:lastIndex]))
      """
      return False

def orElseHandler(words: wordList, wordsBak:wordList, wordLen:int,
              words2:wordList, firstVal:int, 
              semantic:bool, constitutive:bool=False) -> None:
   """Handler function for the Or else (O) component"""

   # Include everything but the last punct if it exists   
   if words[wordLen-1].deprel == "punct":
      lastIndex = wordLen -1
   else:
      lastIndex = wordLen

   # Add the values before the condition
   words2 += words[:firstVal]

   if constitutive:
      orElseComponent = mc.matchingFunctionConstitutive(
            reusePartEoS(wordsBak[firstVal+2:lastIndex], firstVal+2), semantic)
   else:
      orElseComponent = matchingFunction(
            reusePartEoS(wordsBak[firstVal+2:lastIndex], firstVal+2), semantic)
   orElseComponent[0].spaces = 0

   words2.append(Word(
   "","","",0,0,"","","",0,0,1,"O",True,1
   ))
   words2 += orElseComponent
   words2.append(Word("","","",0,0,"","","",0,0,0,"O",True,2))
   # Append the last punct
   if words[wordLen-1].deprel == "punct":
      words2.append(words[wordLen-1])

def oblHandler(words:wordList, i:int, wordLen:int, semantic:bool, 
                               constitutive:bool=False) -> int:
   """Handler for execution constraint (Cex) components detected using the obl dependency"""
   # Check for connections to the obl both before and after
   iBak = i
   scopeStart = i
   scopeEnd = i

   # Find the scope of the component by checking for head related words
   for j in range(wordLen):
      if (ifHeadRelation(words, j, i) 
            and words[j].deprel != "punct"):
         if j > scopeEnd:
            scopeEnd = j
         elif j < scopeStart:
            scopeStart = j
   
   # Look for preceeding acl to include if not annotated with another symbol
   #print(words[scopeStart-1].deprel, words[scopeStart-1].text, words[scopeStart-1].head, scopeStart)
   if (words[scopeStart-1].deprel == "acl" and words[scopeStart-1].symbol==""):
      scopeStart -= 1
      for j in range(scopeStart, -1, -1):
         if words[j].deprel == "case" and words[j].head == words[scopeStart].head:
            scopeStart = j
            break
         if words[j].symbol != "":
            logger.debug("In Cex acl lookbehind found different symbol")
            scopeStart += 1
            break

   if scopeEnd - scopeStart >= minimumCexLength:
      # If the statement is constitutive
      if constitutive:
         # If the obl is connected to a Constituting Entity Property (E,p) component
         # or a Constituting Properties Property (P,p) component
         # extend the component to contain the "new component"
         rootHead = words.getHead(iBak)
         if rootHead.symbol in ["E,p","P,p"]:
            return oblConstitutivePropertyHandler(words, iBak, scopeEnd, rootHead.symbol)
         
         # If the previous word is an acl deprel to a previous property
         elif (words[scopeStart-1].deprel == "acl" and words[scopeStart-2].symbol in ["P,p", "E,p"]):
            words[scopeEnd].setSymbol(words[scopeStart-2].symbol,2)
            if words[scopeStart-2].position == 0:
               words[scopeStart-2].setSymbol(words[scopeStart-2].symbol,1)
            else:
               words[scopeStart-2].setSymbol()
            return scopeEnd
         
         # If the first word is "to" handle it as a Constituting Properties (P) component
         elif words[scopeStart].text.lower() == "to":
            scopeStart += 1
            if scopeEnd-scopeStart >= 1:
               words[scopeStart].setSymbol("P",1)
               words[scopeEnd].setSymbol("P",2)
               words = findInternalLogicalOperators(words, scopeStart, scopeEnd)
            else:
               words[scopeStart].setSymbol("P")
            return scopeEnd
         

      # Check for Date NER in the component
      componentWords = words[scopeStart:scopeEnd+1]

      date = False
      law = False
      for word in componentWords:
         if "DATE" in word.ner:
            date = True
         if "LAW" in word.ner:
            law = True
      
      '''
      if date:
         logger.debug("Date in Execution Constraint (obl): " + 
                     WordsToSentence(componentWords) + " " +
                     str(len(componentWords)))
      else:
         logger.debug("No date in Execution Constraint (obl): " + 
                     WordsToSentence(componentWords) + " " +
                     str(len(componentWords)))
      '''

      # Annotate the words as a Execution Constraint (Cex) component
      # If the current Cex starts with "by" compound it with the previous Cex if adjacent.
      if i-1 >= 0 and words[scopeStart].text == "by" and words[scopeStart-1].symbol == "Cex":
         scopeStart -= 1
         # If previous word is the end of the component         
         if words[scopeStart].position == 2:
            # remove symbol from the previous word
            words[scopeStart].setSymbol()
            # Look for the component start and update the scopeStart
            for j in range(scopeStart-1, -1, -1):
               if words[j].symbol == "Cex":
                  scopeStart = j
                  break    
         # handle semantic annotations
         if semantic:
            if date and not "ctx:tmp" in words[scopeStart].semanticAnnotation:
               words[scopeStart].addSemantic("ctx:tmp")
            if law and not "act:law" in words[scopeStart].semanticAnnotation:
               words[scopeStart].addSemantic("act:law")
      # Else just annotate the component and potential semantic annotations
      else:
         words[scopeStart].setSymbol("Cex", 1)
         if semantic:
            if date:
               words[scopeStart].addSemantic("ctx:tmp")
            if law:
               words[scopeStart].addSemantic("act:law")
      words[scopeEnd].setSymbol("Cex", 2)
      if scopeEnd - scopeStart > 2:
         words = findInternalLogicalOperators(words, scopeStart, scopeEnd)
   
   return scopeEnd

def oblConstitutivePropertyHandler(words:wordList, iBak:int, scopeEnd:int, symbol:str) -> int:
   rootHead:Word = words.getHead(iBak)
   if rootHead.position == 0:
      scopeStart = words[iBak].head
      # If the head is the start of the component find the end, remove its annotation,
      # encapsulate, return
   elif rootHead.position == 1:
      for j in range(rootHead.position+1, scopeStart):
         if words[j].position == 2:
            words[j].setSymbol()
            words[scopeEnd].setSymbol(symbol,2)
            return scopeEnd
   # If the head is the end of the component remove the symbol, encapsulate, return
   else: 
      rootHead.setSymbol()
      words[scopeEnd].setSymbol(symbol)
      return scopeEnd

   if scopeEnd-scopeStart >= 1:
      words[scopeStart].setSymbol(symbol,1)
      words[scopeEnd].setSymbol(symbol,2)
      words = findInternalLogicalOperators(words, scopeStart, scopeEnd)
   else:
      words[scopeStart].setSymbol(symbol)
   return scopeEnd

def attributeHandler(words:wordList, i:int, wordLen:int) -> int:
   """Handler for attribute (A) components detected using the nsubj dependency"""
   #print("Running attributeHandler, ", words[i].text, words[i].deprel, words.getHeadDep(iBak))
   if words[i].pos != "PRON":
      # Look for nmod connected to the word i

      #i = smallLogicalOperator(words, i, "A", wordLen)
      other = False
      for j in range(wordLen):
         if "nmod" in words[j].deprel and ifHeadRelation(words, j, i):
            #print("A with xpos: ", words[j], words[j].xpos)
            #print("Nmod head relation to a: ", words[j], words[i])
            j = smallLogicalOperator(words, j, "A", wordLen)
            other = True
            if i+1 < wordLen and words[i+1].deprel == "appos" and words[i+1].head == i:
               if words[i].position == 2:
                  words[i].setSymbol()
                  words[i+1].setSymbol("A",2)
                  i+=1
               else:
                  words[i].setSymbol("A",1)
                  words[i+1].setSymbol("A",2)
                  i+=1
            # Special case for nmod:poss dependencies followed by the nsubj dependency
            # Only applies when NER is used and detects either an organization or a person 
            # as the nsubj
            # TODO: Reconsider this when more testing data is available
            if words[j].deprel == "nmod:poss" and j+1 == i and  words[i].ner[2:] in ["ORG","PERSON"]:
               words[j].setSymbol("A,p")
               i = smallLogicalOperator(words, i, "A", wordLen)
               return i
      if not other:
         i = smallLogicalOperator(words, i, "A", wordLen)
         if i+1 < wordLen and words[i+1].deprel == "appos" and words[i+1].head == i:
            if words[i].position == 2:
               words[i].setSymbol()
               words[i+1].setSymbol("A",2)
               i+=1
            else:
               words[i].setSymbol("A",1)
               words[i+1].setSymbol("A",2)
               i+=1
   # If the nsubj is a pronoun connected to root then handle it as an attribute
   # This may need to be reverted in the future if coreference resolution is used
   # in that case, the coreference resolution will be used to add the appropriate attribute
   elif words.getHeadDep(i) == "root":
      i = smallLogicalOperator(words, i, "A", wordLen)
      if i+1 < wordLen and words[i+1].deprel == "appos" and words[i+1].head == i:
         if words[i].position == 2:
            words[i].setSymbol()
            words[i+1].setSymbol("A",2)
            i+=1
         else:
            words[i].setSymbol("A",1)
            words[i+1].setSymbol("A",2)
            i+=1

   # (A,p) detection mechanism, might be too specific. 
   # Is overwritten by Aim (I) component in several cases
   if i+1 < wordLen and words[i+1].deprel == "advcl" and words.getHeadDep(i+1) == "root":
      #print("ADVCL")
      words[i+1].setSymbol("A,p")

   #print(WordsToSentence(words))
   return i

def deonticHandler(words:wordList, i:int) -> int:
   """Handler for deontic (D) components detected using the aux dependency"""
   #print("Deontic Handler: ", words[i].text, words[i].deprel, words[i].pos, words[i].xpos)
   if words.getHeadPos(i) == "VERB" or words[i].xpos == "MD":
      #print("Deontic: ", words[i].xpos) 
      #Might be worth looking into deontics that do not have xpos of MD
      # Combine two adjacent deontics if present.
      if i-1 >= 0 and words[i-1].symbol == "D":
         words[i-1].setSymbol("D",1)
         words[i].setSymbol("D",2)
      else:
         # If the head is a word after the deontic encapsualte the words in-between
            """
         if (words[i].head - i) > 1:
            words[i].setSymbol("D",1)
            # Encapsulate everything before the head (head is Aim (I))
            i = words[i].head-1
            if words[i].text in [".",","]:
               i-=1
            words[i].setSymbol("D",2)
         else:
            """
            words[i].setSymbol("D")
   else:
      logger.debug("Deontic, no verb")
   
   #print(words[i+1].text, words[i].text)
   if words[i+1].text.lower() == "not":
      #print("True")
      if words[i].position == 0:
         words[i].position = 1
      else:
         words[i].setSymbol()
      i+=1
      words[i].setSymbol("D", 2)

   #print(WordsToSentence(words[i:i+1]))
   return i

def rootHandler(words:wordList, i:int, wordLen:int) -> int:
   """Handler for Aim (I) components detected using the root dependency"""
   # Potentially unmatch all occurences where the aim is not a verb
   #if words[i].pos != "VERB":
   #   print("Aim is not VERB:", words[i].pos, words[i])
   # Look for logical operators
   iBak = i
   words[i].setSymbol("I")
   i = smallLogicalOperator(words, i, "I", wordLen, True)
   if words[i].position == 0:
      # Look for xcomp dependencies
      k = 0

      for k in range(wordLen):
         if words[k].deprel == "xcomp" and words[k].head == i:
            #print("XComp of I: ", words[k], k, i)
            # If the xcomp is adjacent encapsulate it in the aim component
            if k-i == 2:
               words[i].setSymbol("I",1)
               words[i+2].setSymbol("I",2)
               i = k
               break
            else:
               j = i+1
               while j < k-1:
                  if words[j].head != k:
                     # Add semantic annotation for context based on xcomp
                     # if the xcomp is not adjacent to the aim
                     words[i].text = (words[i].text + " " * words[k].spaces + "[" + 
                                    words[k].text + "]")
                     j = k
                     break
                  j+=1
               if j == k-1:
                  # If the xcomp is adjacent encapsulate it in the aim component
                  words[i].setSymbol("I",1)
                  words[k].setSymbol("I",2)
                  i = k
      # TODO: Test with cop dependency instead of the "be" dictionary based approach
      if iBak-1 > 0 and words[iBak-1].text.lower() == "be":
         words[iBak-1].setSymbol("I",1)
         if words[iBak].position == 0: words[iBak].position = 2
         else: words[iBak].setSymbol()

   # Look for logical operators for inclusion
   lastConj = i
   for j in range(i+1,wordLen):
      if ifHeadRelation(words, j, i):
         if words[j].deprel == "conj":
            lastConj = j
            # advmod, amod
         if not words[j].deprel in ["det","cc","conj"]:
            break
   
   if lastConj != i:
      j = lastConj
      if words[i].position == 2:
         words[i].setSymbol()
         words[j].setSymbol("I",2)
      else:
         words[i].position = 1
         words[j].setSymbol("I",2)

      i = j

   return i

def bindHandler(words:wordList, i:int, wordLen:int) -> int:
   """Handler for indirect object (Bind) components detected using the iobj dependency"""
   iBak = i
   i = smallLogicalOperator(words, i, "Bind", wordLen)

   # If the flag is True combine the object with single word properties preceeding 
   if CombineObjandSingleWordProperty:
      if (words[iBak-1].symbol == "Bind,p" and words[iBak-1].deprel == "amod"
         and words[iBak-1].position == 0):
         if iBak != i:
            words[iBak].setSymbol("", 0)
            words[iBak-1].setSymbol("Bind", 1)
         else:
            words[iBak].setSymbol("Bind", 2)
            words[iBak-1].setSymbol("Bind", 1)

   return i

def bdirHandler(words:wordList, i:int, wordLen:int) -> int:
   """Handler for Direct object (Bdir) components detected using the obj dependency"""
   iBak = i
   i = smallLogicalOperator(words, i, "Bdir", wordLen)
   # Positive lookahead for nmod to include:
   # May need future refinement
   # TODO: Look into positive lookahead vs, handling nmod separately as currently done
   '''
   if words[i].position == 0:
      j=i
      while j < wordLen:
         if words[j].deprel == "nmod" and words[j].head == i:
            if j+1 < wordLen:
               if not ifHeadRelation(words, j+1, j):
                  words[i].setSymbol("Bdir", 1)
                  words[j].setSymbol("Bdir", 2)
                  i = j
               break
            else:
               words[i].setSymbol("Bdir", 1)
               words[j].setSymbol("Bdir", 2)
               i = j
               break
         j += 1
   '''

   # If the flag is True combine the object with single word properties preceeding 
   # the object
   if CombineObjandSingleWordProperty:
      if (words[iBak-1].symbol == "Bdir,p" and words[iBak-1].deprel == "amod"
         and words[iBak-1].position == 0):
         if (words[iBak-2].symbol != "Bdir,p"):
            if iBak != i:
               words[iBak].setSymbol("", 0)
               words[iBak-1].setSymbol("Bdir", 1)
            else:
               words[iBak].setSymbol("Bdir", 2)
               words[iBak-1].setSymbol("Bdir", 1)

   return i

def amodPropertyHandler(words:wordList, i:int, wordLen:int) -> int:
   """Handler for properties detected using the amod dependency. Currently used for 
      Direct object (Bdir), Indirect object (Bind) and Attribute (A) properties (,p)"""
   # If the word is directly connected to an obj (Bdir)
   if words.getHeadDep(i) == "obj":
      i = smallLogicalOperator(words, i, "Bdir,p", wordLen)
      #words[i].setSymbol("Bdir,p")
   # Else if the word is directly connected to an iobj (Bind)
   elif words.getHeadDep(i) == "iobj":
      i = smallLogicalOperator(words, i, "Bind,p", wordLen)
      #words[i].setSymbol("Bind,p")
   # Else if the word is connected to a nsubj connected directly to root (Attribute)
   elif (words.getHeadDep(i) == "nsubj" 
         and (words[words.getHeadId(i)].deprel == "root" or 
         words[words.getHeadId(i)].symbol == "A")):
      i = smallLogicalOperator(words, i, "A,p", wordLen)
      #words[i].setSymbol("A,p")
   return i

def nmodDependencyHandler(words:wordList, i:int, wordLen:int) -> int:
   """Handler for nmod dependency, currently used for Direct object (Bdir) components 
   and its properties"""
   iBak = i
   # Too broad coverage in this case, detected instances which should be included in the main
   # object in some instances, an instance of an indirect object component, and several 
   # overlaps with execution constraints.
   # TODO: Look into nmod inclusion further
   #print("Starting nmoddependencyHandler")
   if words.getHeadSymbol(i) == "Bdir" and words.getHeadPosition(i) in [0,2]:
      #print("Within if")
      #logger.debug("NMOD connected to BDIR")
      # positive lookahead
      firstIndex = i
      doubleNmod = False
      # Find and encapsulate any other nmods connected to the last detected nmod
      for j in range(wordLen):
         if words[j].deprel == "nmod" and words[j].head == i:
            lastIndex = j
            doubleNmod = True
            i = j
      
      # if two or more nmod dependencies are connected then treat it as a Bdir,p
      if doubleNmod:
         # Set the first word after the direct object component as the start of the component
         words[words[firstIndex].head+1].setSymbol("Bdir,p", 1)
         words[lastIndex].setSymbol("Bdir,p", 2)
         i = lastIndex
      else:
         # Set the first word after the direct object component as the start of the component
         if words.getHeadPosition(firstIndex) == 0:
            words.getHead(firstIndex).setSymbol("Bdir", 1)
         else:
            words.getHead(firstIndex).setSymbol("", 0)
         words[i].setSymbol("Bdir", 2)
   return i if i > iBak else iBak

def conditionHandler2(words:wordList, i:int, wordLen:int) -> int:
   """Handler function for the matching and encapsulation of conditions (Cac, Cex)"""
   #print("Running conditionHandler 2")
   firstVal = i
   
   # Go through the statement until the word is connected to the advcl directly or indirectly
   for j in range(i):
      # If connected to the advcl then set firstVal to the id and break the loop
      if ifHeadRelation(words, j, i):
         firstVal = j
         break

   # Go through again from the activation condition++
   # Until the word is no longer connected to the advcl
      
   # Set the lastVal to the current id -1   
   lastIndex = i+1 if i+1 < wordLen else i
   for j in range(lastIndex,wordLen):
      if not ifHeadRelation(words, j, i):
         lastIndex = j-1
         break
   
   if words[firstVal].deprel == "punct":
      firstVal += 1

   #print(words[lastIndex].text, words[lastIndex].deprel)
   if words[lastIndex].deprel == "punct":
      lastIndex -= 1
   #print(words[lastIndex].text, words[lastIndex].deprel)
      
   #print(words[firstVal].text, words[lastIndex].text)

   words[firstVal].setSymbol("Cac", 1)
   words[lastIndex].setSymbol("Cac", 2)

   return lastIndex