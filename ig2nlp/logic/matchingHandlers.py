from utility import *
from logic.matchingUtils import *
from logic.matchingUtilsConstitutive import *

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
   rootHead:Word = getHead(words, iBak)
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

def oblAgentHandler(words:list[Word], word:Word, i:int, wordLen:int) -> int:
   """Handler for obl:agent dependency, currently only used for Constitutive statements: 
   Constitutive function (F) and Constituting properties (P) components"""
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
   return i

def attributeHandler(words:list[Word], i:int, wordLen:int) -> int:
   """Handler for attribute (A) components detected using the nsubj dependency"""
   #print("Running attributeHandler, ", words[i].text, words[i].deprel, getHeadDep(words, iBak))
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
            if words[j].deprel == "nmod:poss" and j+1 == i and words[i].ner[2:] in ["ORG","PERSON"]:
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
   elif getHeadDep(words, i) == "root":
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
   if i+1 < wordLen and words[i+1].deprel == "advcl" and getHeadDep(words, i+1) == "root":
      #print("ADVCL")
      words[i+1].setSymbol("A,p")

   #print(WordsToSentence(words))
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
   if getHeadSymbol(words, i) == "Bdir" and getHeadPosition(words, i) in [0,2]:
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
         if getHeadPosition(words, firstIndex) == 0:
            getHead(words, firstIndex).setSymbol("Bdir", 1)
         else:
            getHead(words, firstIndex).setSymbol("", 0)
         words[i].setSymbol("Bdir", 2)
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
   """Handler for constituted entity (E) components detected using the nsubj dependency"""
   iBak = i
   if words[i].pos != "PRON":
      # Look for nmod connected to the word i
      other = False
      for j in range(wordLen):
         if "nmod" in words[j].deprel and ifHeadRelation(words, j, i):
            #print("A with xpos: ", words[j], words[j].xpos)
            #print("Nmod head relation to a: ", words[j], words[i])
            j = smallLogicalOperator(words, j, "E", wordLen)
            other = True
            if i+1 < wordLen and words[i+1].deprel == "appos" and words[i+1].head == i:
               if words[i].position == 2:
                  words[i].setSymbol()
                  words[i+1].setSymbol("E",2)
                  i+=1
               else:
                  words[i].setSymbol("E",1)
                  words[i+1].setSymbol("E",2)
                  i+=1
      if not other:
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
      
      """
      if words[iBak].symbol == "":
         words[iBak].setSymbol("E")
      """

   # If the nsubj is a pronoun connected to root then handle it as an attribute
   # This may need to be reverted in the future if coreference resolution is used
   # in that case, the coreference resolution will be used to add the appropriate attribute
   elif words[words[i].head].deprel == "root":
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
      if words[iBak-1].text.lower() == "not":
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
   """Handler for nmod dependency, currently used for Constituting Properties (P) components 
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

