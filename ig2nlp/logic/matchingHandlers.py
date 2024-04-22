from utility import *
from logic.matchingUtils import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1


def oblHandler(words:list[Word], i:int, wordLen:int, semantic:bool, 
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
   
   #print(scopeStart, words[scopeStart], scopeStart-1, words[scopeStart-1])
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
            if constitutive: scopeStart += 1
            break
   
   #print(scopeStart, words[scopeStart], scopeStart-1, words[scopeStart-1])

   if scopeEnd - scopeStart >= minimumCexLength:
      # If the statement is constitutive
      if constitutive:
         # If the obl is connected to a Constituting Entity Property (E,p) component
         # or a Constituting Properties Property (P,p) component
         # extend the component to contain the "new component"
         rootHead = getHead(words, iBak)
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
      
         """If Regulative"""
      # If the statement is regulative
      else:
         # If the obl is connected to a regulative property (A,p, Bind,p, Bdir,p)
         rootHead = getHead(words, iBak)
         if (rootHead.symbol in ["A,p","Bdir,p","Bind,p"] and rootHead.position == 0 and
             words[words[i].head+1].text != ","):
            return oblConstitutivePropertyHandler(words, iBak, scopeEnd, rootHead.symbol)

         if (rootHead.deprel == "acl"
             and words[words[i].head+1].text != ","
             and rootHead.symbol in ["Bdir","Bind","Bdir,p","Bind,p"]):
            # Encapsulate the content in-between
            words[scopeEnd].setSymbol(rootHead.symbol,2)
            # Remove annotations in-between
            for j in range(words[i].head+1, scopeEnd-1):
               words[j].setSymbol()

            # Check head position and update it accordingly
            if rootHead.position == 0:
               rootHead.position = 1
            elif rootHead.position == 2:
               rootHead.setSymbol()
            return scopeEnd
            
      """
      # Check the head for xcomp relation, if so encapsulate everything
      if getHeadDep(words, i) == "xcomp":
         headId = words[i].head
         # Find preceeding mark
         
         if words[headId+1].deprel == "mark":
            # Remove old annotations
            for j in range(headId+1,i):
               words[j].setSymbol()
            words[headId+1].setSymbol("Cex",1)
            words[i].setSymbol("Cex",2)
            return i
         # TODO: Find any further words to include
      """

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

def oblConstitutivePropertyHandler(words:list[Word], iBak:int, scopeEnd:int, symbol:str) -> int:
   """Handler for obl deprels connected to property annotations. 
   Handles scope extension for property annotations."""
   rootHead:Word = getHead(words, iBak)
   if rootHead.position == 0:
      scopeStart = words[iBak].head
      # If the head is the start of the component find the end, remove its annotation,
      # encapsulate, return
   elif rootHead.position == 1:
      for j in range(rootHead.position+1, scopeEnd):
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

def oblAgentHandler(words:list[Word], word:Word, i:int, wordLen:int, constitutive:bool) -> int:
   """Handler for obl:agent dependency, currently only used for Constitutive statements: 
   Constitutive function (F) and Constituting properties (P) components"""
   if constitutive:
      # TODO: Look into other use cases for obl:agent
      #print("obl:agent", word)
      head = words[word.head]
      if head.symbol != "" and head.symbol != "F":
         if head.position == 0:
            head.position = 1
         else:
            # TODO: might need to check for other annotations within
            head.position = 1
            for j in range(head.position+1, i-1):
               if words[j].symbol != "":
                  words[j].setSymbol()
         word.setSymbol(head.symbol, 2)
         i = includeConj(words, i, wordLen)
         #print(WordsToSentence)
         #print(word)
      elif head.symbol == "F":
         if head.position == 1:
            for j in range(head.position+1, i-1):
               if words[j].position == 2:
                  start = j+1
                  break
         else: start = word.head+1
         words[start].setSymbol("P",1)
         word.setSymbol("P",2)
         i = includeConj(words, i, wordLen)
      else:
         head.setSymbol("P",1)
         word.setSymbol("P",2)
         i = includeConj(words, i, wordLen)
      #print("OBL AGENT ", word.text, words[word.head].text, words[word.head].symbol, 
      #      words[word.head].pos)
   else:
      head = getHead(words, i)
      if head.symbol in ["A,p","Bdir,p","Bind,p"] and head.position == 0:
         lastVal = i
         for j in range(i+1, wordLen):
            deprel = words[j].deprel
            if (deprel in ["case","nmod","amod","advmod","cc","conj","nmod","det",
                           "nmod:tmod","nummod","nsubj","obl","dep","punct","appos"] 
               and ifHeadRelation(words, j, i)):
               lastVal = j
            else: break
         head.position = 1
         words[lastVal].setSymbol(head.symbol, 2)
         return lastVal
      elif words[i].pos == "PROPN":
         i = attributeHandler(words, i, wordLen)
      #TODO: look into covering more cases of the obl:agent dependency in regulative statements
      #print("obl:agent", words[i].text)
      #words[i].text = "agent: "+words[i].text + " pos: " + words[i].pos
   return i

def deonticHandler(words:list[Word], i:int) -> int:
   """Handler for deontic (D) components detected using the aux dependency"""
   #print("Deontic Handler: ", words[i].text, words[i].deprel, words[i].pos, words[i].xpos)
   if getHeadPos(words, i) == "VERB" or words[i].xpos == "MD":
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

def rootHandler(words:list[Word], i:int, wordLen:int) -> int:
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

def bindHandler(words:list[Word], i:int, wordLen:int) -> int:
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

def bdirHandler(words:list[Word], i:int, wordLen:int) -> int:
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

def amodPropertyHandler(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for properties detected using the amod dependency. Currently used for 
      Direct object (Bdir), Indirect object (Bind) and Attribute (A) properties (,p)"""
   # If the word is directly connected to an obj (Bdir)
   if getHeadDep(words, i) == "obj":
      i = smallLogicalOperator(words, i, "Bdir,p", wordLen)
      #words[i].setSymbol("Bdir,p")
   # Else if the word is directly connected to an iobj (Bind)
   elif getHeadDep(words, i) == "iobj":
      i = smallLogicalOperator(words, i, "Bind,p", wordLen)
      #words[i].setSymbol("Bind,p")
   # Else if the word is connected to a nsubj connected directly to root (Attribute)
   elif (getHeadDep(words, i) == "nsubj" 
         and (words[getHeadId(words, i)].deprel == "root" or 
         words[getHeadId(words, i)].symbol == "A")):
      i = smallLogicalOperator(words, i, "A,p", wordLen)
      #words[i].setSymbol("A,p")
   return i

def nmodDependencyHandler(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for nmod dependency, currently used for Direct object (Bdir) components 
   and its properties"""
   iBak = i
   # Too broad coverage in this case, detected instances which should be included in the main
   # object in some instances, an instance of an indirect object component, and several 
   # overlaps with execution constraints.
   # TODO: Look into nmod inclusion further
   #print("Starting nmoddependencyHandler")

   # TODO: consider removing the edgeCase detection, may be overfitted
   if getHeadSymbol(words, i) == "Bdir" and getHeadPosition(words, i) in [0,2]:
      #print("Within if")

      edgeCase = False
      start = i
      # Positive lookbehind for mark and ","
      for j in range(i-1,-1,-1):
         #print(words[i].deprel, words[i].symbol)
         if ifHeadRelation(words, j, i):
            if words[j].deprel not in ["advmod","amod","det","mark","case","punct"]:
               edgeCase = False
               break
            elif words[j].symbol != "":
               edgeCase = False
               break
            elif words[j].deprel == "punct":
               edgeCase = True
               start = j+1
               break
         else:
            edgeCase = False
            break
      
      #print(edgeCase, words[j].deprel, words[j].text)

      if edgeCase:
         words[start].setSymbol("Bdir,p", 1)
         end = i
         # Positive lookahead for inclusions
         for j in range(i+1,wordLen):
            if not ifHeadRelation(words, j, i):
               end = j-1
               break
         
         words[end].setSymbol("Bdir,p", 2)
         
         if end-start > 2:
            findInternalLogicalOperators(words, start, end)

         return end

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
         for j in range(words[i].head+1,i):
            #print(words[j].text)
            if words[j].text == ",":
               return i if i > iBak else iBak
         # Look for logical operators to include
         end = i
         j = i+1
         while j < wordLen:
            if ifHeadRelation(words, j, i):
               if not words[j].deprel in ["amod","advmod","det","cc","conj"]:
                  break
               if words[j].deprel == "conj":
                  end = j
               j += 1
            else:
               break
         if end > i: i = end
         if getHeadPosition(words, firstIndex) == 0:
            getHead(words, firstIndex).setSymbol("Bdir", 1)
         else:
            getHead(words, firstIndex).setSymbol("", 0)
         words[i].setSymbol("Bdir", 2)
         # Handle internal operators
         if i - words[firstIndex].head > 2:
            words = findInternalLogicalOperators(words,firstIndex,i)
   return i if i > iBak else iBak

def conditionHandler2(words:list[Word], i:int, wordLen:int) -> int:
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

def constitutedEntityHandler(words:list[Word], i:int, wordLen:int) -> int:
   #Handler for constituted entity (E) components detected using the nsubj dependency
   iBak = i

   # If the nsubj is a pronoun
   if words[i].pos == "PRON":
      if words[words[i].head].deprel == "root":
         i = smallLogicalOperator(words, i, "E", wordLen)
         if i+1 < wordLen and words[i+1].deprel == "appos" and words[i+1].head == i:
            if words[i].position == 2:
               words[i].setSymbol()
               words[i+1].setSymbol("E",2)
               i+=1
            else:
               words[i].setSymbol("E",1)
               words[i+1].setSymbol("E",2)
               i+=1

      # (E,p) detection mechanism, might be too specific. 
      # Is overwritten by Aim (I) component in several cases
      if i+1 < wordLen and words[i+1].deprel == "advcl" and words[words[i+1].head].deprel == "root":
         #print("ADVCL")
         words[i+1].setSymbol("E,p")

      # TODO: consider turning this into a property instead (E,p)
      prevWord = words[iBak-1]
      startWord = words[iBak]
      if prevWord.deprel == "amod" and prevWord.symbol == "":
         if startWord.symbol == "E":
            prevWord.setSymbol("E", 1)
            if startWord.position == 1:
               startWord.setSymbol()
            elif startWord.position == 0:
               startWord.setSymbol("E",2)
            else:
               logger.warning(
            "constitutedEntityHandler found invalid scoping of Entity in amod dependency handling")
               prevWord.setSymbol()
   # Else
   else:
      # Positive lookahead for potential deprels to include
      lastVal = i
      propertyStart = -1
      for j in range(i+1, wordLen):
         deprel = words[j].deprel
         if (deprel in ["case","nmod","amod","advmod","cc","conj","nmod","det",
                        "nmod:tmod","nummod","nsubj","obl","dep","punct","appos"] 
             and ifHeadRelation(words, j, i)):
            # Look for property boundaries (E,p) using nmod:tmod and nummod dependencies
            if propertyStart == -1:
               if deprel == "nmod:tmod":
                  if words[j-1].head >= j:
                     propertyStart = j-1
                  else:
                     propertyStart = j
               elif deprel == "nummod" and getHeadDep(words, j) == "nmod":
                  if words[j-1].head >= j:
                     propertyStart = j-1
                  else:
                     propertyStart = j

            lastVal = j
         else: break

      # If the component contains multiple words
      if lastVal > i:
         # If a property boundary is detected
         if propertyStart != -1:
            # If the Entity contains multiple words encapsualte them
            if (propertyStart-1) > i:
               words[i].setSymbol("E",1)
               words[propertyStart-1].setSymbol("E",2)
               if (propertyStart-1 - i) > 1:
                  words = findInternalLogicalOperators(words,i,propertyStart-1)
            else:
               words[i].setSymbol("E")

            # If the property contains multiple words encapsualte them
            if lastVal > propertyStart:
               words[propertyStart].setSymbol("E,p",1)
               words[lastVal].setSymbol("E,p",2)
               if (lastVal-1 - propertyStart) > 1:
                  words = findInternalLogicalOperators(words,propertyStart,lastVal)
            else:
               words[propertyStart].setSymbol("E,p")

         else:
            words[i].setSymbol("E",1)
            words[lastVal].setSymbol("E",2)
            if (lastVal - i) > 1:
               words = findInternalLogicalOperators(words,i,lastVal)

      else:
         words[i].setSymbol("E")
      
      # Positive lookbehind for properties (amod, advmod)
      if words[iBak-1].deprel in ["amod","advmod"]:
         words[iBak-1].setSymbol("E,p")

      # Include preceeding properties in the component
      backTracker = iBak
      while words[backTracker-1].symbol == "E,p":
         if words[backTracker-2].deprel != "cc":
            words[backTracker-1].setSymbol()
            backTracker -= 1
         else:
            break
      
      if backTracker != iBak:
         if words[iBak].position == 0:
            words[iBak].position = 2
         else:
            words[iBak].setSymbol()

         words[backTracker].setSymbol("E", 1)

      i = lastVal

   return i

def attributeHandler(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for attribute (A) components detected using the nsubj dependency"""
   iBak = i

   # If the nsubj is a pronoun
   if words[i].pos == "PRON":
      if words[words[i].head].deprel == "root":
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
      if i+1 < wordLen and words[i+1].deprel == "advcl" and words[words[i+1].head].deprel == "root":
         #print("ADVCL")
         words[i+1].setSymbol("A,p")

      # TODO: consider turning this into a property instead (A,p)
      prevWord = words[iBak-1]
      startWord = words[iBak]
      if prevWord.deprel == "amod" and prevWord.symbol == "":
         if startWord.symbol == "A":
            prevWord.setSymbol("A", 1)
            if startWord.position == 1:
               startWord.setSymbol()
            elif startWord.position == 0:
               startWord.setSymbol("A",2)
            else:
               logger.warning(
            "constitutedEntityHandler found invalid scoping of Entity in amod dependency handling")
               prevWord.setSymbol()
   # Else
   else:
      # Positive lookahead for potential deprels to include
      lastVal = i
      componentStart = -1
      for j in range(i+1, wordLen):
         deprel = words[j].deprel
         if (deprel in ["case","nmod","amod","advmod","cc","conj","nmod","det",
                        "nmod:tmod","nummod","nsubj","obl","dep","punct","appos"] 
             and ifHeadRelation(words, j, i)):
            
            #if words[j].deprel == "det":
            #   words[j].spaces = 0
            #   words[j].text = ""
            # Look for property boundaries (E,p) using nmod:tmod and nummod dependencies
            # TODO: test "to" as well
            if deprel == "case" and words[j].text.lower() in ["by","of"]:
               if words[j+1].deprel == "det":
                  componentStart = j+2
               else:
                  componentStart = j+1

            lastVal = j
         else: break

      #print("A: ", words[i].text, words[componentStart].text, words[lastVal].text)

      # If the component contains multiple words
      if lastVal > i:
         # If a property boundary is detected
         if componentStart != -1:
            # If the attribute contains multiple words encapsualte them
            if lastVal > componentStart:
               words[componentStart].setSymbol("A",1)
               words[lastVal].setSymbol("A",2)
               for k in range(componentStart, lastVal):
                  if words[k].deprel == "det":
                     words[k].spaces = 0
                     words[k].text = ""
               if (lastVal-1 - componentStart) > 1:
                  words = findInternalLogicalOperators(words,componentStart,lastVal)
            else:
               if componentStart+1 < wordLen:
                  if (words[componentStart+1].deprel == "root" 
                     or words[words[componentStart+1].head].deprel == "root"):
                     words[componentStart].setSymbol("A")

         else:
            words[i].setSymbol("A",1)
            words[lastVal].setSymbol("A",2)
            for k in range(i, lastVal):
               if words[k].deprel == "det":
                  words[k].spaces = 0
                  words[k].text = ""
            if (lastVal - i) > 1:
               words = findInternalLogicalOperators(words,i,lastVal)


      else:
         # Check for obl:agent related to acl
         if words[i+1].deprel == "acl" and i == words[i+1].head:
            for j in range(i+2,wordLen):
               # If obl agent is found then mark it as an attribute and return
               if words[j].head == i+1 and words[j].deprel == "obl:agent":
                  # TODO: consider removing the I and Bdir annotations from here
                  # or encapsulating the subsentence as an activation condition
                  words[j].setSymbol("A")
                  words[i+1].setSymbol("I")
                  words[i].setSymbol("Bdir")
                  #print("Returning:", j)
                  return j

         # Else just handle the component
         if words[i-1].deprel == "nmod:poss" and words[i-1].head == i:
            if words[i].pos != "PROPN":
               words[i-1].setSymbol("A")
            else:
               words[i-1].setSymbol("A,p")
               words[i].setSymbol("A")
         else:
            words[i].setSymbol("A")

      i = lastVal

   #print("Returning:", i)
   return i

def modalHandler(words:list[Word], i:int) -> int:
   """Handler for modal (M) components detected using the aux dependency"""
   #if words[words[i].head].pos == "VERB":
      #print("Modal: ", words[i].xpos) 
      #Might be worth looking into Modals that do not have xpos of MD
      # Combine two adjacent Modals if present.
   #print(words[i].xpos, words[i].text)
   if words[i].xpos != "MD":
      logger.debug("aux no MD xpos: " + words[i].text + " | pos" + words[i].pos + 
                   " | xpos" + words[i].xpos)
      i = constitutiveFunctionAuxHandler(words, len(words), i)
      #print(words[i].text, words[i].symbol,words[i].position)
      return i
   
   if words[i].text == "be":
      words[i].setSymbol("F")
      # Positive lookahead
      # TODO: check this in a larger dataset potentially, 
      # for now this is only applied in constitutiveFunctionAuxHandler
      #if words[i+1].deprel == "det":
      #   words[i+1].setSymbol("P")
      #   i += 1
      return i
   
   # If previous word is a Modal, encapsulate both
   if words[i-1].symbol == "M":
      words[i-1].setSymbol("M",1)
      words[i].setSymbol("M",2)
   
   else:
      '''
      if (words[i].head - i) > 1:
         words[i].setSymbol("M",1)
         i = words[i].head-1
         words[i].setSymbol("M",2)
      else:
         words[i].setSymbol("M")
   '''

      words[i].setSymbol("M")

   print(words[i+1])
   if words[i+1].text.lower() == "not":
      #print("True")
      if words[i].position == 0:
         words[i].position = 1
      else:
         words[i].setSymbol()
      i+=1
      words[i].setSymbol("M", 2)
   print(words[i])

   return i


def constitutiveFunctionAuxHandler(words:list[Word], wordLen:int, i:int) -> int:
   """Handler for Constitutive Function (F) components detected using the aux dependency"""
   #print("Running constitutiveFunctionAuxHandler")
   word = words[i]
   #print(word.text, word.pos, word.xpos, word.deprel)
   
   #if wordLen > i+3:
   #   print(words[i].text,words[i+1].text,words[i+2].text,words[i+3].text)
   #   print(words[i].deprel,words[i+1].deprel,words[i+2].deprel,words[i+3].deprel)
   if i+1 < wordLen and words[i+1].deprel == "root":
      if (wordLen > i+3 and words[i+2].deprel == "mark" 
         and words[i+3].deprel == "xcomp" and words[i+3].head == i+1):
            words[i].setSymbol("F",1)
            words[i+3].setSymbol("F",2)
            #print(words[i+3])
            return i+3
   '''
      if wordLen > i+2 and words[i+2].deprel == "xcomp":
         words[i].setSymbol("M",1)
         words[i+1].setSymbol("M",2)
         words[i+2].setSymbol("F")
         return i+2
   '''
   words[i].setSymbol("F")

   if word.text == "are":
      if i+1 < wordLen:
         if words[i+1].deprel == "conj":
            words[i+1].setSymbol("P")
         elif words[i+1].deprel == "amod" or words[i+1].deprel == "advmod":
            words[i+1].setSymbol("P,p")
            if words[i+1].head == i+2:
               words[i+2].setSymbol("P")
               i += 2
            else:
               words[words[i+1].head].setSymbol("P")
               words[words[i+1].head-1].setSymbol("P,p",2)
               words[i+1].setSymbol("P,p",1)
               i = words[i+1].head
         elif words[i+1].deprel == "root" and words[i+1].pos == "VERB":
            words[i].position = 1
            words[i+1].setSymbol("F",2)
            #print(WordsToSentence(words))
            return i+1
         else:
            #print(words[i+1].pos, words[i].text, "caseThing")
            words[i+1].setSymbol("P")
            i+=1
      else:
         #print(words[i+1].pos, words[i].text, "caseThing")
         words[i+1].setSymbol("P")
         i+=1

   elif word.text == "be":

      if i+1 < wordLen and words[i+1].deprel == "det":
         i += 2
         iBak = i
         if words[i].deprel == "amod" or words[i].deprel == "advmod":
            i = smallLogicalOperator(words, i, "P,p", len(words))

         if words[iBak].head != i+1:
            logger.warning("P,p head is not adjacent")
         
         i+=1

         # Positive lookahead for nmod deprels to include
         possibleDeprels = ["appos","punct","case","det","nmod","amod"]
         for j in range(i+1, len(words)):
            # Find a nmod and all connected words if it exists
            if words[j].deprel == "nmod" and words[j].head == i:
               k = j
               for j in range(k+1, len(words)):
                  #print(words[j].text, words[j].deprel)
                  # Validate that the word is connected to the nmod deprel
                  if ifHeadRelation(words, j, k):
                     # Validate the deprel of the current word
                     if not (words[j].deprel in possibleDeprels):
                        # if not in possible deprels include everything up to this point
                        print("NOT IN DEPRELS", words[j].deprel)
                        words[i-1].setSymbol("P",1)
                        words[j-1].setSymbol("P",2)
                        i = j-1
                        return i
                  else:
                     # If not connected to the head then include everything up to this point
                     #print("Not head related")
                     if j-1 - i-1 == 1:
                        words[i].setSymbol("P",1)
                        words[j-1].setSymbol("P",2)
                     else:
                        words[i-1].setSymbol("P",1)
                        words[j-1].setSymbol("P",2)
                     i = j-1
                     return i
               # Exception
               if j != len(words)-1:
                  #print("EXCEPTION")
                  words[i].setSymbol("P")
               else:
               # Include everything if at the end of the list of words
                  #print("NOT IN DEPRELS", words[j].deprel)
                  words[i-1].setSymbol("P",1)
                  words[j].setSymbol("P",2)
                  i = j

               return i
         
         # If not nmod
         words[i].setSymbol("P")
         
      #print("be")
   else:
      #print("Exception:", word.text)
      if i-1 >= 0 and words[i-1].symbol == "F":
         if words[i-1].position != 2:
            words[i-1].position = 1
         else:
            words[i-1].position = 0
         words[i].setSymbol("F",2)

   # Positive lookahead, 
   return i

def rootHandlerConstitutive(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for Constitutive Function (F) components detected using the root dependency"""
   # Potentially unmatch all occurences where the Constitutive Function is not a verb
   #if words[i].pos != "VERB":
   #   print("Constitutive Function is not VERB:", words[i].pos, words[i])
   words[i].setSymbol("F")
   iBak = i
   # Look for logical operators
   i = smallLogicalOperator(words, i, "F", wordLen, True)
   if words[i].position != 0:
      # Check for preceeding auxiliary or cop dependency
      if iBak-1 >= 0:
         if words[iBak-1].deprel == "aux:pass" or words[iBak-1].deprel == "cop":
            if words[iBak].position == 1:
               words[iBak].setSymbol()
            elif words[iBak].position == 0:
               words[iBak].setSymbol("F",2)
            else:
               logger.warning("Error finding scope of Constitutive Function in rootHandlerConstitutive")
               return i
            # Check if the word overlaps with the end of another symbol. If so move the end back one word.
            if words[iBak-1].position == 2:
               if words[iBak-2].position == 1:
                  words[iBak-2].position = 0
               else:
                  words[iBak-2].position = 2
                  words[iBak-2].symbol = words[iBak-1].symbol
            words[iBak-1].setSymbol("F",1)
   else:
      # Look for xcomp dependencies
      k = 0

      for k in range(wordLen):
         if words[k].deprel == "xcomp" and words[k].head == i:
            #print("XComp of I: ", words[k], k, i)
            # If the xcomp is adjacent encapsulate it in the aim component
            if k-i == 2:
               words[i].setSymbol("F",1)
               words[i+2].setSymbol("F",2)
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
                  words[i].setSymbol("F",1)
                  words[k].setSymbol("F",2)
                  i = k
   # Check for preceeding auxiliary or cop dependency
   if iBak-1 >= 0:
      if words[iBak-1].deprel == "aux:pass" or words[iBak-1].deprel == "cop":
         if words[iBak].position == 1:
            words[iBak].setSymbol()
         elif words[iBak].position == 0:
            words[iBak].setSymbol("F",2)
         else:
            logger.warning("Error finding scope of Constitutive Function in rootHandlerConstitutive")
            return i
         # Check if the word overlaps with the end of another symbol. If so move the end back one word.
         if words[iBak-1].position == 2:
            if iBak-2 >= 0:
               if words[iBak-2].position == 1:
                  words[iBak-2].position = 0
               else:
                  words[iBak-2].position = 2
                  words[iBak-2].symbol = words[iBak-1].symbol
         words[iBak-1].setSymbol("F",1)

      # Check for preceeding negation "not"
      if words[iBak-1].text.lower() == "not" and words[iBak-1].symbol in ["","F"]:
         # If preceeding Constitutive Function (F)
         if iBak-2 >= 0 and words[iBak-2].symbol == "F":
            if words[iBak-2].position == 0:
               words[iBak-2].position = 1
            else:
               words[iBak-2].setSymbol()
            if words[iBak].position == 0:
               words[iBak].position == 2
            else:
               words[iBak].setSymbol()
         
         # If not preceeding Constitutive Function (F)
         else:
            words[iBak-1].setSymbol("F",1)
            if words[iBak].position == 0:
               words[iBak].position == 2
            else:
               words[iBak].setSymbol()

         if words[i].position == 0: words[i].position = 2


   '''
   if words[i+1].deprel == "case" and words[iBak-1].text == "be":
         if words[i].position == 2:
            words[i].setSymbol()
            words[i+1].setSymbol("F",2)
         else:
            words[i].setSymbol("F",1)
            words[i+1].setSymbol("F",2)
         i += 1
         print(words[i])
   '''
   return i

def amodPropertyHandlerConstitutive(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for properties detected using the amod dependency. Currently used for 
      Constituting Properties (P) and Constituted Entity (E) properties (,p)"""
   # Head of the word to check for the component it is a potential property of
   head = words[i].head
   # If the word is directly connected to an obj (P)
   if words[head].deprel == "obj":
      i = smallLogicalOperator(words, i, "P,p", wordLen)
   # Else if the word is directly connected to an iobj (P)
   elif words[head].deprel == "iobj":
      i = smallLogicalOperator(words, i, "P,p", wordLen)
   # Else if the word is connected to a nsubj connected directly to root (Attribute)
   elif (words[head].deprel == "nsubj" 
         and (words[words[head].head].deprel == "root" or 
         words[words[head].head].symbol == "E")):
      i = smallLogicalOperator(words, i, "E,p", wordLen)
   return i

def constitutingPropertiesHandler(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for Constituting Properties (P) components 
      detected using the obj and iobj dependencies"""
   iBak = i
   #print(WordsToSentence(words),"\n", words[i])
   i = smallLogicalOperator(words, i, "P", wordLen)

   # If the flag is True combine the object with single word properties preceeding 
   # the object
   if CombineObjandSingleWordProperty:
      if (iBak-1 >= 0 and words[iBak-1].symbol == "P,p" and words[iBak-1].deprel == "amod"
         and words[iBak-1].position == 0):
         if (iBak-2 >= 0 and words[iBak-2].symbol != "P,p"):
            if iBak != i:
               # Remove old annotation start
               words[iBak].setSymbol()
               words[iBak-1].setSymbol("P", 1)
            else:
               words[iBak-1].setSymbol("P", 1)
               words[iBak].setSymbol("P", 2)
   #print(WordsToSentence(words),"\n", words[i])
   return i

def nmodDependencyHandlerConstitutive(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for nmod dependency, used for Constituting Properties (P) components 
   and its properties (,p)"""
   #words[i].setSymbol()
   # Too broad coverage in this case, detected instances which should be included in the main
   # object in some instances, an instance of an indirect object component, and several 
   # overlaps with execution constraints.
   # TODO: Look into nmod inclusion further
   if words[words[i].head].symbol == "P" and words[words[i].head].position in [0,2]:
      # Remove old annotation if present
      words[i].setSymbol()
      #logger.debug("NMOD connected to Constituting Properties")
      # positive lookahead
      firstIndex = i
      doubleNmod = False
      # Find and encapsulate any other nmods connected to the last detected nmod
      for j in range(i, wordLen):
         if words[j].deprel == "nmod" and words[j].head == i:
            lastIndex = j
            doubleNmod = True
            i = lastIndex
      
      # if two or more nmod dependencies are connected then treat it as a P,p
      if doubleNmod:
         # Set the first word after the direct object component as the start of the component
         if words[firstIndex].head+1 < lastIndex:
            words[words[firstIndex].head+1].setSymbol("P,p", 1)
            words[lastIndex].setSymbol("P,p", 2)
            i = lastIndex
      else:
         # Set the first word after the direct object component as the start of the component
         if words[words[firstIndex].head].position == 0:
            words[words[firstIndex].head].setSymbol("P", 1)
         else:
            # Remove the symbol from the head
            words[words[firstIndex].head].setSymbol()
         words[i].setSymbol("P", 2)
   
   #print(WordsToSentence(words))
   #print(words[i])
   return i

def csubjHandler(words:list[Word], i:int, wordLen:int, constitutive:bool) -> int:
   """Handler for the csubj dependency, used for Aim (I) and Constitutive Functino (F) components.
   In constitutive statements Modal (M) components are handled additionally."""
   head = getHead(words, i)
   if not constitutive:
      # Find "I" bounds:
      if head.symbol == "I":
         if head.position == 2:
            start = -1
            for j in range(words[i].head-1, -1, -1):
               if words[j].symbol == "I":
                  start = j
                  break
            if start != -1:
               words[start].setSymbol()
               head.setSymbol()
         elif head.position == 0:
            head.setSymbol()
      i = rootHandler(words, i, wordLen)
   else:
      if head.deprel == "root":
         # Find "F" bounds:
         if head.symbol == "F":
            if head.position == 2:
               start = -1
               for j in range(words[i].head-1, -1, -1):
                  if words[j].symbol == "F":
                     start = j
                     break
               if start != -1:
                  # Check for preceeding expl to include
                  if words[start-1].deprel == "expl":
                     words[start-1].setSymbol("M",1)
                     words[start].setSymbol()
                     head.symbol = "M"
                  else:
                     words[start].symbol = "M"
                     head.setSymbol("M",2)
               elif head.position == 0:
                  head.symbol = "M"
      i = rootHandlerConstitutive(words, i, wordLen)
   return i
   
def aclRelclHandler(words:list[Word], i:int, wordLen:int) -> int:
   """Handles acl:relcl dependencies, used to handle properties (,p) 
   of Direct Object (Bdir) and Indirect Object (Bind) components."""
   HeadSymbol = getHeadSymbol(words, i)
   if HeadSymbol in ["Bdir","Bind"]:
      start = words[i].head+1
      if words[start].text == ",": start +=1

      end = i
      for j in range(i+1,wordLen):
         if not ifHeadRelation(words, j, i):
            end = j-1

      for j in range(start+1, end-1):
         words[j].setSymbol()
      
      words[start].setSymbol(HeadSymbol+",p",1)
      words[end].setSymbol(HeadSymbol+",p",2)

      return end
   else:
      print("ACLRELCL NOT HANdLED")
   return i

def aclHandler(words:list[Word], i:int, wordLen:int, constitutive:bool=False) -> int:
   """Handles acl dependencies"""
   word = words[i]
   head = getHead(words, i)
   headId = word.head
   # If regulative
   if not constitutive:
      # (A,p) Attribute property detection 2
      if words[word.head].symbol == "A":
         word.setSymbol("A,p")
      # (Bdir,p) Direct object property detection 3
      # TODO: Reconsider in the future if this is accurate enough
      # There are currently false positives, but they should be mitigated by better
      # Cex component detection
         
      elif i-1 >= 0 and head.symbol == "Bdir":
         if words[i-1].symbol == "Bdir":
            word.setSymbol("Bdir,p")
         
         elif not words[i-1].symbol == "" or not words[words[i].head+1].symbol == "":
            return i
         
         elif words[headId+1].text.lower() != "for":
            if head.position == 0:
               head.position = 1
               words[i].setSymbol("Bdir", 2)
         else:
            if i - headId+1 > 0:
               words[headId+1].setSymbol("Bdir,p",1)
               words[i].setSymbol("Bdir,p",2)
            else:
               words[i].setSymbol("Bdir,p")


         
         #else:
         #   if words[words[i].head+1].symbol == "":
         #      i = aclRelclHandler(words,i,wordLen)
         
         """
         else:
            headId = words[i].head
            if getHeadPosition(words,i) in [0,2]: 
               start = headId+1
            else:
               start = findComponentEnd(words, headId, "Bdir")+1
            end = start
            for j in range(i+1,wordLen):
               if not ifHeadRelation(words, j, start):
                  end = j-1

            if end - start > 2:
               for j in range(start+1,end-1):
                  words[j].setSymbol()
               
            if end != start:
               words[start].setSymbol("Bdir,p",1)
               words[end].setSymbol("Bdir,p",2)
            else:
               words[start].setSymbol("Bdir,p")
            i=end
         """
   # If constitutive
   else:
      # TODO: Reconsider in the future if this is accurate enough
      # There are currently false positives, but they should be mitigated by better
      # Cex component detection

      # (E,p) Constituted Entity Property detection 2
      if words[word.head].symbol == "E":
         word.setSymbol("E,p")
      # (P,p) Constituting Properties property detection 3
      elif words[word.head].symbol == "P" and words[i-1].symbol == "P":
         word.setSymbol("P,p")

      elif words[word.head].symbol == "":
         # Check if within a component
         for j in range(word.head, -1, -1):
            word2 = words[j]
            if word2.symbol != "":
               if word2.position == 1:
                  if word2.symbol == "E":
                     word.setSymbol("E,p")
                  elif word2.symbol == "P":
                     word.setSymbol("P,p")
               break
   return i