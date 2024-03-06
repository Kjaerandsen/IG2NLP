import time
import copy
import logic.matchingFunction as m
from utility.utility import *
from logic.matchingUtils import *
from logic.matchingUtilsConstitutive import *
from logic.classifier import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1
#semanticAnnotations = False
numberAnnotation = False
coref = True

def matchingHandlerConstitutive(words:list[Word], semantic:bool) -> list[Word]:
   """takes a list of words, performs annotations using the matching function and returns 
   a formatted string of annotated text"""
   words = compoundWordsHandler(words)
   words = matchingFunctionConstitutive(words, semantic)
   if coref: words = corefReplaceConstitutive(words, semantic)
   if semantic and numberAnnotation: words = attributeSemantic(words)
   # Handle cases where a logical operator is included in a component without a matching wor
   logicalOperatorImbalanced(words)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   handleScopingIssues(words)
   print("Constitutive coverage: ", coverage(words))
   return WordsToSentence(words)

def matchingFunctionConstitutive(words:list[Word], semantic:bool) -> list[Word]:
   """takes a list of words with dependency parse and pos-tag data.
      Returns a list of words with IG Script notation symbols."""
   wordLen = len(words)
   wordsBak = copy.deepcopy(words)
   words2 = []

   # Look for conditions only first, if enabled remove the advcl case from the matching below
   #for i, word in enumerate(words):
   #   if word.deprel == "advcl":
   #      if m.conditionHandler(words, wordsBak, i, wordLen, words2, True, True):
   #         return words2

   i = 0
   while i < wordLen:
      word = words[i]
      deprel = word.deprel

      #print(words[words[i].head], words[i].deprel, words[i].text)

      match deprel:
         # (Cac, Cex) Condition detection
         case "advcl":
            if m.conditionHandler(words, wordsBak, i, wordLen, words2, 
                             semantic, True):
               return words2
            
         # (P) Constituting Properties / (E,p) Constituted Entity detection
         case "obj":
            #print(WordsToSentence(words),"\n", words[i])
            if words[word.head].deprel == "acl" and words[word.head].symbol == "E,p":
               words[word.head].setSymbol("E,p",1)
               word.setSymbol("E,p",2)
            #elif words[word.head].deprel == "root":
            #   i = smallLogicalOperator(words, i, "E", wordLen)
            #   i = constitutedEntityHandler(words, i, wordLen)
            else:
               i = constitutingPropertiesHandler(words, i, wordLen)

         # (P) Constituting Properties detection 2
         case "iobj":
            i = constitutingPropertiesHandler(words, i, wordLen)

         # (F) Constitutive Function detection
         case "root":
            i = rootHandlerConstitutive(words, i, wordLen)

         # Else if the word has an amod dependency type, check if the head is a symbol
         # that supports properties, if so, the word is a property of that symbol
         # (P,p, E,p)   
         case "amod":
            i = amodPropertyHandlerConstitutive(words, i, wordLen)
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

         # Constituting Properties handling (P), (P,p)
         case "nmod":
            i = nmodDependencyHandlerConstitutive(words, i, wordLen)
            # TODO: Revisit and test
            #else if words[word.head].symbol == "E":
            #   print("\nnmod connected to Constituted Entity(E): ", word)

         # (P,p) Constituting Properties Property detection 2
         case "nmod:poss":
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
               m.orElseHandler(words, wordsBak, wordLen, words2, i, semantic, True)
               return words2
         # Advmod of Aim is correlated with execution constraints (Cex)
         # Might be too generic of a rule.
         # TODO: Revisit and test
         case "advmod":
            if words[word.head].symbol == "F":
               #print("\nadvmod connected to Aim(I): ", word)
               if i+1 < wordLen:
                  if words[i+1].deprel == "punct":
                     word.setSymbol("Cex")
         
         # (Cex) Execution constraint detection
         case "obl":
            i = m.executionConstraintHandler(words, i, wordLen, semantic, True)
         case "obl:tmod":
            # Old implementation used
            # i = words[i].head
            i = m.executionConstraintHandler(words, i, wordLen, semantic, True)
         case "obl:agent":
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

         case "cop":
            #print("cop",word.symbol,word.pos,word.text, word.xpos, word.pos)
            if word.pos == "AUX":
               i = constitutiveFunctionAuxHandler(words, wordLen, i)

         # Default, for matches based on more than just a single deprel
         case _:
            # Print out more complex dependencies for future handling
            #if ":" in deprel:
            #   if deprel != "aux:pass" and deprel != "obl:tmod":
            #      print("\n", '":" dependency: ',words[i], "\n")
            
            # (E) Constituted Entity detection
            # TODO: Consider specyfing which nsubj dependencies specifically to include
            if "nsubj" in deprel:
               i = constitutedEntityHandler(words, i, wordLen)

               # TODO: look into the line below
               if words[word.head].deprel == "ccomp":
                  logger.debug("NSUBJ CCOMP OBJ")

            # (M) Modal detection
            #elif words[word.head].deprel == "root" and "aux" in deprel:
            elif "aux" in deprel:
               #print(words[i].text, words[i].deprel)
               i = modalHandler(words, i)
               #print("After modal, ", WordsToSentence(words))
               #print(i)

            elif (deprel != "punct" and deprel != "conj" and deprel != "cc"
                 and deprel != "det" and deprel != "case"):
               logger.debug("Unhandled dependency: " + deprel)
      
      #print("\nNew word", words[i])
      # Iterate to the next word
      #print(WordsToSentence(words),"\n")
      i += 1

   return words

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
   i = smallLogicalOperator(words, i, "F", wordLen)
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