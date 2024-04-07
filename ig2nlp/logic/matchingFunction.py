import copy
from utility import *
from logic.classifier import *
from logic.matchingHandlers import *
from logic.matchingUtils import comments

minimumCexLength = 1
numberAnnotation = False
coref = True

def matchingHandler(words:list[Word], semantic:bool, 
                    constitutive:bool=False, args:dict={}) -> tuple[list[Word], str]:
   """takes a list of words, performs annotations using the matching function and returns 
   a formatted string of annotated text"""
   global comments
   keyList = []
   for key in comments: keyList.append(key)
   for key in keyList: del(comments[key])
   del(keyList)

   # Handle the optional args
   if "coref" in args:
      global coref
      coref = args["coref"]
   if "semantic" in args:
      semantic = args["semantic"]
   if "semanticNumber" in args:
      global numberAnnotation
      numberAnnotation = args["semanticNumber"]

   words = compoundWordsHandler(words)
   words = logicalOperatorHandler(words)
   words = matchingFunction(words, semantic, constitutive)
   if coref: words = corefReplace(words, semantic, constitutive)
   if semantic and numberAnnotation: words = entitySemantic(words, constitutive)
   # Handle cases where a logical operator is included in a component without a matching word
   logicalOperatorImbalanced(words)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   handleScopingIssues(words)
   """
   if not constitutive:
      print("Regulative coverage: ", coverage(words))
   else:
      print("Constitutive coverage: ", coverage(words))
   """
   
   # Go through all comments, add them to the comment output with a newline
   comment = ""
   commentList = [comments[key] + "\n" for key in comments]
   for commentItem in commentList:
      comment += commentItem

   return WordsToSentence(words), comment

def matchingFunction(words:list[Word], semantic:bool, 
                     constitutive:bool = False) -> list[Word]:
   """takes a list of words with dependency parse and pos-tag data.
      Returns a list of words with IG Script notation symbols."""
   wordLen = len(words)
   wordsBak = copy.deepcopy(words)
   words2 = []

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

      #print(getHead(words, i), words[i].deprel, words[i].text)

      match deprel:
         # (Cac, Cex) Condition detection 
         case "advcl":
            if conditionHandler(words, wordsBak, i, wordLen, words2, semantic, constitutive):
               return words2
            else:
               i = conditionHandler2(words, i, wordLen)
         
                  
         case "ccomp":
            if not constitutive:
               if ccompHandler(words, wordsBak, i, wordLen, words2, semantic):
                  return words2


         case "obj":
            # (Bdir) Object detection
            if not constitutive:
               i = bdirHandler(words, i, wordLen)
            
            # (P) Constituting Properties / (E,p) Constituted Entity detection
            else:
               if words[word.head].deprel == "acl" and words[word.head].symbol == "E,p":
                  words[word.head].setSymbol("E,p",1)
                  word.setSymbol("E,p",2)
               #elif words[word.head].deprel == "root":
               #   i = smallLogicalOperator(words, i, "E", wordLen)
               #   i = constitutedEntityHandler(words, i, wordLen)
               else:
                  i = constitutingPropertiesHandler(words, i, wordLen)

         case "iobj":
            # (Bind) Indirect object detection
            if not constitutive:
               i = bindHandler(words, i, wordLen)
            # (P) Constituting Properties detection 2
            else:
               i = constitutingPropertiesHandler(words, i, wordLen)

         case "root":
            # (I) Aim detection
            if not constitutive:
               i = rootHandler(words, i, wordLen)
            # (F) Constitutive Function detection
            else:
               i = rootHandlerConstitutive(words, i, wordLen)

         case "csubj":
            i = csubjHandler(words, i, wordLen, constitutive)

         case "amod":
            # Else if the word has an amod dependency type, check if the head is a symbol
            # that supports properties, if so, the word is a property of that symbol
            # (Bdir,p, Bind,p, A,p)   
            if not constitutive:
               i = amodPropertyHandler(words, i, wordLen)
            
            # Else if the word has an amod dependency type, check if the head is a symbol
            # that supports properties, if so, the word is a property of that symbol
            # (P,p, E,p)   
            else:
               i = amodPropertyHandlerConstitutive(words, i, wordLen)

         case "acl":
            aclHandler(words, i, wordLen, constitutive)

         case "nmod":
            # Direct object handling (Bdir), (Bdir,p)
            if not constitutive:
               i = nmodDependencyHandler(words, i, wordLen)
               # TODO: Revisit and test
               #else if words[word.head].symbol == "A":
               #   print("\nnmod connected to Attribute(A): ", word)
            
            # Constituting Properties handling (P), (P,p)
            else:
               i = nmodDependencyHandlerConstitutive(words, i, wordLen)
               # TODO: Revisit and test
               #else if words[word.head].symbol == "E":
               #   print("\nnmod connected to Constituted Entity(E): ", word)

         
         case "nmod:poss":
            # (Bdir,p) Direct object property detection 2
            if not constitutive:
               if getHeadDep(words, i) == "obj" and word.head == i+1:
                  # Check if there is a previous amod connection and add both
                  if i-1 >= 0 and words[i-1].deprel == "amod" and words[i-1].head == i:
                     words[i-1].setSymbol("Bdir,p", 1)
                     word.setSymbol("Bdir,p", 2)
                  # Else only add the Bdir,p
                  else:
                     word.setSymbol("Bdir,p")
               #else:
                  #print("\nWord is nmod:poss: ", word)
                 
            # (P,p) Constituting Properties Property detection 2         
            else:
               if words[word.head].deprel == "obj" and word.head == i+1:
                  # Check if there is a previous amod connection and add both
                  if words[i-1].deprel == "amod" and words[i-1].head == i:
                     words[i-1].setSymbol("P,p", 1)
                     word.setSymbol("P,p", 2)
                  # Else only add the P,p
                  else:
                     word.setSymbol("P,p")
               #else:
                  #print("\nWord is nmod:poss: ", word)
                     
         # (O) Or else detection
         case "cc":
            if i+1 < wordLen and words[i+1].text == "else":
               orElseHandler(words, wordsBak, wordLen, words2, i, semantic, constitutive)
               return words2
            
         # Advmod of Aim / Const. func. is correlated with execution constraints (Cex)
         # Might be too generic of a rule.
         # TODO: Revisit and test
         case "advmod":
            if not constitutive:
               if getHeadSymbol(words, i) == "I":
                  #print("\nadvmod connected to Aim(I): ", word)
                  if i+1 < wordLen:
                     if words[i+1].deprel == "punct":
                        word.setSymbol("Cex")
            else:
               if words[word.head].symbol == "F":
                  #print("\nadvmod connected to Aim(I): ", word)
                  if i+1 < wordLen:
                     if words[i+1].deprel == "punct":
                        word.setSymbol("Cex")
         
         # (Cex) Execution constraint detection
         case "obl":
            i = oblHandler(words, i, wordLen, semantic, constitutive)
         case "obl:tmod":
            # Old implementation used
            # i = words[i].head
            i = oblHandler(words, i, wordLen, semantic, constitutive)

         # (P) Constituting Properties detection
         case "obl:agent":
            i = oblAgentHandler(words, word, i, wordLen, constitutive)

         case "cop":
            # (F) Constitutive function and (P) Constituting properties detection
            if constitutive:
               #print("cop",word.symbol,word.pos,word.text, word.xpos, word.pos)
               if word.pos == "AUX":
                  i = constitutiveFunctionAuxHandler(words, wordLen, i)

         case "acl:relcl":
            if not constitutive:
               i = aclRelclHandler(words, i, wordLen)

         # Default, for matches based on more than just a single deprel
         case _:
            # Print out more complex dependencies for future handling
            #if ":" in deprel:
            #   if deprel != "aux:pass" and deprel != "obl:tmod":
            #      print("\n", '":" dependency: ',words[i], "\n")
            
            # TODO: Consider specyfing which nsubj dependencies specifically to include
            if "nsubj" in deprel:
               # (A) Attribute detection
               if not constitutive:
                  i = attributeHandler(words, i, wordLen)

                  # TODO: look into the line below
                  if getHeadDep(words, i) == "ccomp":
                     logger.debug("NSUBJ CCOMP OBJ")

               # (E) Constituted Entity detection
               else:
                  i = constitutedEntityHandler(words, i, wordLen)

                  # TODO: look into the line below
                  if words[word.head].deprel == "ccomp":
                     logger.debug("NSUBJ CCOMP OBJ")

            
            elif "aux" in deprel:
               # (D) Deontic detection
               if not constitutive:
                  if getHeadDep(words, i) == "root":
                     i = deonticHandler(words, i)

               # (M) Modal detection
               else:
                  i = modalHandler(words, i)

            elif (deprel != "punct" and deprel != "conj" and deprel != "cc"
                 and deprel != "det" and deprel != "case"):
               logger.debug("Unhandled dependency: " + deprel)
      
      #print(words[i].text, words[i].symbol, words[i].position)
      # Iterate to the next word
      #print(WordsToSentence(words))
      i += 1

   return words

def conditionHandler(words:list[Word], wordsBak:list[Word], i:int, 
                     wordLen:int, words2:list[Word], semantic:bool, 
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

      condition = matchingFunction(
         reusePartSoS(copy.deepcopy(wordsBak[:lastIndex]), lastIndex), semantic, constitutive)

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

      contents = matchingFunction(
            reusePartEoS(words[lastIndex+1:], lastIndex+1), semantic, constitutive)

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
         words2 += matchingFunction(reusePartSoS(words[:firstVal], firstVal),
                                            semantic, constitutive)
      else:
         words2 += words[:firstVal]
         condition = matchingFunction(
               reusePartMoS(copy.deepcopy(wordsBak[firstVal:lastIndex]), firstVal, lastIndex),
               semantic, constitutive)

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
         
         contents = matchingFunction(
            reusePartEoS(wordsBak[lastIndex+1:lastVal], lastIndex+1), semantic, constitutive
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

      return False
   
def ccompHandler(words:list[Word], wordsBak:list[Word], i:int, 
                     wordLen:int, words2:list[Word], semantic:bool) -> bool:
   """Handler function for the matching and encapsulation of Direct Object (Bdir) components"""
   firstVal = i
   # Update to check if there are any overlapping annotations
   # Go through the statement until the word is connected to the advcl directly or indirectly
   inComp = False
   nullified = True
   for j in range(i):
      # If connected to the advcl then set firstVal to the id and break the loop
      if ifHeadRelation(words, j, i):
         if inComp and words[j].position == 2:
            inComp = False
         #elif words[j].symbol == "Cac":
         #   inComp = True
         #   nullified = True
         #   firstVal = -1
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
      
   if firstVal == 0:
      contents = []

      condition = matchingFunction(
         reusePartSoS(copy.deepcopy(wordsBak[:lastIndex]), lastIndex), semantic, False)

      if validateNested(condition, False):
         words2.append(Word(
         "","","",0,0,"","","",0,0,0,"Bdir",True,1
         ))
         condition[0].spaces = 0
         words2 += condition
         words2.append(Word("","","",0,0,"","","",0,0,0,"Bdir",True,2))
         words2.append(words[lastIndex])
      else:
         words2 += wordsBak[:lastIndex]
         words2[0].setSymbol("Bdir",1)
         words2[lastIndex-1].setSymbol("Bdir",2)
         words2.append(words[lastIndex])
         if lastIndex - firstVal > 2:
            words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)

      contents = matchingFunction(
            reusePartEoS(words[lastIndex+1:], lastIndex+1), semantic, False)

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
      firstVal+=1
      if words[firstVal].text == ",":
         firstVal+=1
      #print(words[firstVal].text, words[firstVal].symbol, words[firstVal].position)
      if words[firstVal].symbol in ["Cac","Cex"]:
         # If one word component, go to the next word
         if words[firstVal].position == 0:
            firstVal +=1
         else:
            # Else find the end of the component and update the firstVal to the subsequent word
            for j in range(firstVal+1,wordLen):
               if words[j].symbol == words[firstVal].symbol:
                  firstVal = j+1
                  break
         #print(words[firstVal].text, words[firstVal].symbol, words[firstVal].position)
      # Ensure that the start is not a comma
      if words[firstVal].text == ",":
         firstVal+=1
      #print(words[firstVal].text, words[firstVal].symbol, words[firstVal].position)

      #print("First val was not id 0 and deprel was mark", words[lastIndex])
      # Do the same as above, but also with the words before this advcl
      contents = []

      # Add the values before the condition
      #if parseFirst:
      #   words2 += matchingFunction(reusePartSoS(words[:firstVal], firstVal),
      #                                      semantic, False)
      #else:
      words2 += words[:firstVal]
      condition = matchingFunction(
            reusePartMoS(copy.deepcopy(wordsBak[firstVal:lastIndex]), firstVal, lastIndex),
            semantic, False)

      j = 0

      if validateNested(condition, False):
         words2.append(Word(
         "","","",0,0,"","","",0,0,1,"Bdir",True,1
         ))
         condition[0].spaces = 0
         words2 += condition
         words2.append(Word("","","",0,0,"","","",0,0,0,"Bdir",True,2))
         words2.append(words[lastIndex])
      else:
         words2 += wordsBak[firstVal:lastIndex]
         words2[firstVal].setSymbol("Bdir",1)
         words2[lastIndex-1].setSymbol("Bdir",2)
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
         
         contents = matchingFunction(
            reusePartEoS(wordsBak[lastIndex+1:lastVal], lastIndex+1), semantic, False
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

      return False

def orElseHandler(words: list[Word], wordsBak:list[Word], wordLen:int,
              words2:list[Word], firstVal:int, 
              semantic:bool, constitutive:bool=False) -> None:
   """Handler function for the Or else (O) component"""

   # Include everything but the last punct if it exists   
   if words[wordLen-1].deprel == "punct":
      lastIndex = wordLen -1
   else:
      lastIndex = wordLen

   # Add the values before the condition
   words2 += words[:firstVal]

   orElseComponent = matchingFunction(
         reusePartEoS(wordsBak[firstVal+2:lastIndex], firstVal+2), semantic, constitutive)

   orElseComponent[0].spaces = 0

   words2.append(Word(
   "","","",0,0,"","","",0,0,1,"O",True,1
   ))
   words2 += orElseComponent
   words2.append(Word("","","",0,0,"","","",0,0,0,"O",True,2))
   # Append the last punct
   if words[wordLen-1].deprel == "punct":
      words2.append(words[wordLen-1])