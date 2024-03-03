from os import getenv
from dotenv import load_dotenv
import stanza
import logging

# Word for handling words,
# takes the variables from the nlp pipeline output, and additional variables for handling components
class Word:
   """Word class for handling words, with nlp pipeline data and IG Script notation annotation data
   """
   # Use slots for faster access
   # Limits variables of the class to only the defined attributes
   __slots__ = ("text", "pos", "deprel", "head", "id", "lemma", "xpos", "feats",
             "start", "end", "spaces", "symbol", "nested", "position", "ner",
             "logical", "corefid", "coref", "corefScope", "isRepresentative",
             "semanticAnnotation")

   def __init__(self, text:str, pos:str, deprel:str, head:int, 
             id:int, lemma:str, xpos:int, feats:str,
             start=0, end=0, spaces=0, symbol="", nested = False, position = 0, ner="", 
             logical=0, corefid = -1, coref = "", corefScope = 0, isRepresentative=False,
             semanticAnnotation="") -> None:
      
      self.id = id
      self.text = text
      self.deprel = deprel
      self.head = head-1
      self.start = start
      self.end = end
      self.pos = pos
      self.xpos = xpos
      self.lemma = lemma
      self.symbol = symbol
      self.nested = nested
      self.position = position
      self.spaces = spaces
      if feats != None: self.feats = feats
      else: self.feats = ""
      self.ner = ner
      self.logical = logical # 1 for left and right bracket, 2 for left, 3 for right, 4 for the operator
      self.coref = coref
      self.corefid = corefid
      self.corefScope = corefScope
      self.isRepresentative = isRepresentative
      self.semanticAnnotation = semanticAnnotation
      
   def buildString(self) -> None:
      """Builds the contents as a component with brackets, 
      the symbol and proper spacing in string form"""
      
      output = " " * self.spaces
      if self.symbol != "":
         if self.position == 2:
            if self.nested:
               output += self.text + "}"
            else:
               output += self.text + ")"

         else:
            output += self.symbol
            if self.semanticAnnotation != "":
               output += "["+self.semanticAnnotation+"]"
            if self.nested:
               if self.position == 0:
                  output += "{"+self.text+"}"
               elif self.position == 1:
                  output += "{" + self.text
            else:
               if self.position == 0:
                  output += "("+self.text+")"
               elif self.position == 1:
                  output += "(" + self.text
      else:
         output += self.text

      return output

   def toLogical(self) -> None:
      """Converts the text of the Word to a logical operator i.e. 'and' -> '[AND]'"""

      if self.logical == 0:
         self.text = "[" + self.text.upper() + "]"
         self.logical = 4
   
   def setSymbol(self, symbol:str="", position:int=0, nested=False) -> None:
      """Set the symbol of a Word, 
      position 0 for single word component, 
      position 1 for the start of the component, 
      position 2 for the end.
      Nested decides whether to use '()' or '{}' brackets."""

      self.symbol = symbol
      self.nested = nested
      self.position = position
   
   # Function for combining two subsequent words into one
   # Direction is a bool, True is left to right, False is right to left
   # The direction defines which start and end position to keep, and the text concatenation order
   def combineWords(self, otherWord:"Word", direction:bool):
      """Takes another word and a direction, combines the contents of the two words. 
      direction True for right into left, False for left into right"""

      if direction:
         self.end = otherWord.end
         self.text = self.text + " " * otherWord.spaces + otherWord.text

      else:
         self.start = otherWord.start
         self.text = otherWord.text + " " * self.spaces + self.text
         self.spaces = otherWord.spaces

   def addSemantic(self, annotation:str):
      """Takes a semantic annotation and 
      appends it to the list of semantic annotations in the Word"""

      if self.semanticAnnotation == "":
         self.semanticAnnotation = annotation

      else:
         self.semanticAnnotation += "," + annotation

   def toJSON(self) -> dict:
      """Create a JSON Object from a Word instance (for JSON serialization)"""

      output:dict = {}
      output["id"] = self.id
      output["text"] = self.text
      output["deprel"] = self.deprel
      output["head"] = self.head
      output["start"] = self.start
      output["end"] = self.end
      output["pos"] = self.pos
      output["xpos"] = self.xpos
      output["lemma"] = self.lemma
      output["symbol"] = self.symbol
      output["nested"] = self.nested
      output["position"] = self.position
      output["spaces"] = self.spaces
      output["feats"] = self.feats
      output["ner"] = self.ner
      output["logical"] = self.logical
      output["coref"] = self.coref
      output["corefid"] = self.corefid
      output["corefScope"] = self.corefScope
      output["isRepresentative"] = self.isRepresentative
      output["semanticAnnotation"] = self.semanticAnnotation

      return output

   def __str__(self):
      return("Word: "+ self.text + "\n pos: "+ self.pos + " | " + self.xpos  
            + " | deprel: "+ str(self.deprel) + " | id: " + str(self.id)
            + " | head: " + str(self.head) 
            + "\nLemma: " + self.lemma + " | Symbol: " + self.symbol + " "
            + str(self.position) + " " + str(self.nested) + " | NER:" + self.ner 
            + "\nFeats: " + self.feats + "\n")

def wordFromDict(input:dict) -> Word:
   """Create a Word class instance from a dict (for JSON serialization)"""

   output = Word(
      input["text"],
      input["pos"],
      input["deprel"],
      input["head"]+1, # Plus one as the creation of a Word class instance uses head-1
      input["id"],
      input["lemma"],
      input["xpos"],
      input["feats"],
      input["start"],
      input["end"],
      input["spaces"],
      input["symbol"],
      input["nested"],
      input["position"],
      input["ner"],
      input["logical"],
      input["corefid"],
      input["coref"],
      input["corefScope"],
      input["isRepresentative"],
      input["semanticAnnotation"]
   )

   return output

def convertWordFormat(words:list) -> list[Word]:
   """ Takes the words from the Stanza nlp pipeline, converts the words and data into a list of the
   Word class"""

   i = 0
   wordLen = len(words)

   customWords = []

   while i < wordLen:
      token = words[i].parent
      # This may need separate handling for MWT's to handle the BIE formatting
      if token.multi_ner != None and token.multi_ner[0] != 'O':
         if len(token.multi_ner) > 1 and token.multi_ner[0] != token.multi_ner[1]:
               print("Different annotations: ",token.multi_ner[0], ", ", token.multi_ner[1])
         #print("Ner: ", token.multi_ner, token.text)

      # If no start char then it is a mwt
      # Handle the words of the mwt then iterate
      if words[i].start_char == None:

         # Get the amount of words to handle
         tokenSize = len(token.id)-1

         tokenText = token.text

         startChar = token.start_char
         endChar = startChar + len(words[i].text)

         wordText = tokenText[:endChar]
         tokenText = tokenText[len(words[i].text):]

         if i > 0:
            spaces = startChar - customWords[i-1].end
         else:
            spaces = 0

         addToCustomWords(customWords,words[i], wordText, startChar,endChar,spaces)
         customWords[i].ner = words[i].parent.multi_ner[0]
         i+=1

         # TODO: look into the statement below
         j=0
         while j < tokenSize:
            word = words[i]

            startLoc = tokenText.find(word.text)

            spaces = startLoc
            startChar = endChar + spaces
            endChar = startChar + len(word.text)

            wordText = tokenText[startChar:endChar]
            tokenText = tokenText[endChar:]
            
            addToCustomWords(customWords, words[i], wordText, startChar, endChar, spaces)
            customWords[i].ner = words[i].parent.multi_ner[0]
            i+=1
            j+=1

         # Go to the next iteration
         continue
      
      # Else calculate the number of spaces and add the word to the list
      if i > 0:
         spaces = words[i].start_char - customWords[i-1].end
      else:
         spaces = 0

      addToCustomWords(customWords, words[i], words[i].text, words[i].start_char, 
                   words[i].end_char, spaces)
      customWords[i].ner = words[i].parent.multi_ner[0]

      if words[i].coref_chains != None and len(words[i].coref_chains) > 0:
         #print("\n\nNEW WORD\n\n")
         coref = words[i].coref_chains[0]
         #print(coref.__dict__.keys())
         #print(coref.__dict__)
         #print(coref.is_start)
         #print(coref.is_end)
         #print(coref.is_representative)
         #print(coref.chain.__dict__.keys())
         #print(coref.chain.__dict__)
         #print(coref.chain.index)
         #print(coref.chain.representative_text)
         #print(coref.chain.representative_index)
         #for mention in coref.chain.mentions:
         #   print(mention.__dict__.keys())
         #   print(mention.__dict__)

         customWords[i].coref = coref.chain.representative_text
         customWords[i].corefid = coref.chain.index
         if coref.is_start and coref.is_end:
            scope = 0
         elif not coref.is_start and coref.is_end:
            scope = 2
         elif coref.is_start and not coref.is_end:
            scope = 1
         customWords[i].corefScope = scope
         customWords[i].isRepresentative = coref.is_representative

         #print("\n\nCOREF is ", customWords[i].coref, coref.chain.representative_text)
         '''
         customWords[i].corefid = coref.index
         customWords[i].coref = coref.representative_text
         if coref.is_start and coref.is_end:
            scope = 0
         elif not coref.is_start and coref.is_end:
            scope = 2
         elif coref.is_start and not coref.is_end:
            scope = 1
         customWords[i].scope = scope
         '''

      i += 1

   return customWords

# Simple function for appending to the customWords list. Takes text, start and end parameters 
# to facilitate multi word tokens(MWTs).
def addToCustomWords(
      customWords:list[Word], word, text:str, start:int, end:int, spaces:int) -> None:
   """Appends a Word to a list of Word objects. 
   Takes a Word, text, start, end and spaces parameters"""

   customWords.append(
         Word(
            text,
            word.pos,
            word.deprel,
            word.head,
            word.id,
            word.lemma,
            word.xpos,
            word.feats,
            start,
            end,
            spaces
         ))

# Middleware function for compounding words (multi-word expressions) into single words
# Converts the word datatype to the custom class and runs the compoundWords function twice
def compoundWordsHandler(words:list) -> list[Word]:
   """Middleware function for processing words of the Word class,
   combines compound words in the list to single words"""

   words = compoundWords(words)
   # For compound (punct or cc) conj x relations, where one or more of the same cc are present
   words = compoundWordsConj(words)

   return words

# Takes the words from the nlp pipeline and combines combine words to a single word
# Also converts the datatype to the Word class
def compoundWords(words:list[Word]) -> list[Word]:
   """Basic compound words handling for lists of the Word class, 
   combines simple compound words with their respective counterparts"""

   wordLen = len(words)
   i = 0
   #print("type is: ", type(words[0]), " " , wordLen)
   while i < wordLen:
      # Compound of three words in the form compound, punct, word
      # Combines the punct and the compound first, then the main function combines the rest
      # the compound and the word
      if words[i].deprel == "compound" and abs(words[i].head - i) == 2:
         if i < words[i].head:
            if words[i+1].deprel == "punct":
               i, wordLen = removeWord(words, i+1, wordLen, 1)
               i-=1

      # If the word is a compound word
      elif words[i].deprel == "compound" and words[i].head == i+1: 
         i, wordLen = removeWord(words, i, wordLen)
         i-=1
      
      elif (words[i].deprel == "case" and words[i].head == i-1 
           and words[i].pos == "PART"):
         # Add the PART case (i.e with "state" and "'s" -> "state's")
         #words[i-1].text = words[i-1].text + words[i].text
         i, wordLen = removeWord(words, i, wordLen, 1)

      
      # If the word is a "PART" case dependency
      elif words[i].deprel == "punct" and words[i].head == i+1:
         if (i+2 < wordLen and words[i+2].deprel == "punct" and 
            words[i+2].head == i+1):
            # Combine the punct and following word
            i, wordLen = removeWord(words, i, wordLen)

      # If the word is a compound part of the previous word, combine the previous and the current
      elif words[i].deprel == "compound:prt" and words[i].head == i-1:
         i, wordLen = removeWord(words, i, wordLen, 1)
      i += 1

   return words

def compoundWordsConj(words:list[Word]) -> list[Word]:
   """Compound words handling for conj dependencies of the form compound cc conj root"""

   wordLen = len(words)
   i = 0
   while i < wordLen:
      if words[i].deprel == "compound" and words[words[i].head].deprel == "obj":
         i, _, wordLen = compoundWordsConjHelper(words, i, wordLen)
      i += 1
   return words

def compoundWordsConjHelper(words:list[Word], i:int, wordLen:int) -> None:
   """Helper function performing the logic for compoundWordsConj"""

   start = i
   end = words[i].head
   ccLocs = []
   ccType = ""
   punctLocs = []
   conjLocs = [i]

   endRel = words[end].deprel
   if start > end:
      print("compoundHandler: start > end")
      return start, False, wordLen
   # Look for specific pattern:
   '''
   compound, (optional punct), cc, conj, compound
   or
   compound, (optional punct), conj, (optional punct), cc, conj, compound
   (repeated punct, conj n times before the compound)
   '''
   for i in range(start+1, end):
      #logger.debug("Word: " + words[i].text + " " + words[i].deprel)
      if words[i].deprel != "punct" and words[i].deprel != "cc" and words[i].deprel != "conj":
         #print("compoundHandler: not punct cc or conj deprel")
         return start, False, wordLen
      elif words[i].deprel == "cc":
         #logger.debug("Found cc: "+ words[i].text + " " + words[i].deprel)
         ccLocs.append(i)
         if ccType == "":
            #logger.debug("Adding cc text")
            ccType = words[i].text
         else:
            if ccType != words[i].text:
               logger.warning(
            "utiliy.compoundHandler: Detected several different types of logical operators.")
               return start, False, wordLen
      elif words[i].deprel == "punct":
         if words[i+1].deprel == "cc":
            words[i].text = ""
         else:
            punctLocs.append(i)
      else:
         conjLocs.append(i)

   if len(ccLocs) == 0 or ccType == "":
      #print(
      #      "compoundHandler did not detect a logical operator.")
      return start, False, wordLen
   
   if len(conjLocs) == 0:
      return start, False, wordLen
   
   else:
      for punct in punctLocs:
         words[punct].text = words[ccLocs[0]].text
         words[punct].spaces = 1
         words[punct].deprel = "cc"
      conjLocs = conjLocs[:len(conjLocs)-1]

      for conj in conjLocs:
         #print("Word in conjLocs: " + words[conj].text)
         words[conj].text = words[conj].text + " [" + words[end].text + "]"
         #words[conj].deprel = endRel
      
      # Combine second last word with last word
      _, wordLen = removeWord(words, end-1, wordLen)
      end = end-1
      
      # Change the heads
      # the first word should have the head of the last word of the head
      words[start].head = words[end].head
      words[start].deprel = endRel
      # the last word should have the first word as the head
      words[end].head = start
      words[end].deprel = "conj"

      # Every conj should have the first word as the head
      if len(conjLocs) > 1:
         for conjLoc in conjLocs[1:]:
            words[conjLoc].head = start
      
      for word in words:
         if word.head == end:
            word.head = start

   return end, True, wordLen

# Takes a list of words, an id, the length of the list of words and a direction
# Combines the word with the next (0) or 
# previous (1) word and removes the extra word from the list of words
def removeWord(words:list[Word], i:int, wordLen:int, direction=0) -> None:
   """ Takes a list of words, a location, the length of the list and a 
   direction 0 = left, 1 = right. Combines the word with the next in the given direction, then 
   removes the extra words."""

   if direction == 0:
      if i == wordLen-1:
         raise Exception(
            'removeWord called with Left to Right direction and id == wordLen-1'
         )
      id = i+1
      words[id].combineWords(words[i], False)

   else:
      if i == 0:
         raise Exception(
               'removeWord called with Left to Right direction and id == wordLen-1'
            )
      id = i
      words[id-1].combineWords(words[i], True)

   # Go through the words and adjust the connections between the words to account
   # for the combination of compound words into single words
   for j, word in enumerate(words):
      # Adjust the head connections to take into account the compounding of two elements
      if word.head+1 > id:
         word.head -= 1
      # Adjust the id's to take into account the removal of the compound word
      if j >= i:
         word.id -=  1

   # Remove the extra word
   del words[i]
   return i-1, wordLen-1

def addWord(words:list[Word], i:int, wordText:str) -> None:
   """Appends a word to a list of words in the location with the index of i"""
   
   for word in words:
      #print(word.head-1, word.head)
      if word.head >= i and word.head != -1:
         word.head += 1
      
      if word.id > i:
         word.id += 1

   newWord = []
   newWord.append(Word(wordText,"","",0,i,"","","",0,0,words[i].spaces))
   words = words[:i] + newWord + words[i:]

   return words

def tokenToText(tokens:list) -> None:
   """Takes a list of tokens, returns the output text contained within."""
   
   output = ""
   for token in tokens:
      output += str(token)

   # Remove leading space if present
   if output[0] == " ":
      output = output[1:]

   outputLen = len(output)
      # Remove leading space if present
   if output[outputLen-2] == " ":
      output = output[:outputLen-2] + output[outputLen-1]

   return output

# Builds the final annotated statement or reconstructs the base statement.
def WordsToSentence(words:list[Word], stripFormatting:bool=False) -> str:
   """Takes a list of Word class instances, returns their content as text in the form of 
   a formatted output string with IG Script Notation syntax if present."""

   i = 0
   sentence = ""

   for word in words:
      if stripFormatting:
         word.setSymbol()
      sentence += word.buildString()
      i += 1
   
   return sentence

# For the End of Statement text
def reusePartEoS(words:list[Word], firstVal:int) -> list[Word]:
   """Function for reusing a subset of a list of Words for matching components.
   Sets all connections to words before the index of firstVal to 'root' 
   dependencies and their headId to 0"""

   outsideCount = 0

   for word in words:
      if word.head < firstVal:
         word.head = -1
         word.deprel = "root"
         outsideCount += 1
      else:
         word.head -= firstVal
   
   if outsideCount == 0:
      logger.warning("utility: reusePartEoS found no root dependency")

   elif outsideCount > 1:
      logger.warning("utility: reusePartEoS found multiple root dependencies")

   return words

# For the Start of Statement text
def reusePartSoS(words:list[Word], lastVal:int) -> list[Word]:
   """Function for reusing a subset of a list of Words for matching components.
   Sets all connections to words after the index of lastVal to 'root' 
   dependencies and their headId to 0"""

   outsideCount = 0

   for word in words:
      if word.head > lastVal:
         word.head = -1
         word.deprel = "root"
         outsideCount += 1

   if outsideCount == 0:
      logger.warning("utility: reusePartSoS found no root dependency")

   elif outsideCount > 1:
      logger.warning("utility: reusePartSoS found multiple root dependencies")

   return words

# For the Middle of a Statement text
def reusePartMoS(words:list[Word], firstVal:int, lastVal:int) -> list[Word]:
   """Function for reusing a subset of a list of Words for matching components.
   Sets all connections to words before the index of firstVal or after lastVal to 'root' 
   dependencies and their headId to 0"""

   outsideCount = 0

   for word in words:
      if word.head > lastVal or word.head < firstVal:
         word.head = -1
         word.deprel = "root"
         outsideCount += 1
      else:
         word.head -= firstVal

   if outsideCount == 0:
      logger.warning("utility: reusePartMoS found no root dependency")

   elif outsideCount > 1:
      logger.warning("utility: reusePartMoS found multiple root dependencies")

   return words

def loadEnvironmentVariables() -> dict:
   """Function that loads all environment variables from a ".env" file or 
   the environment variables"""

   load_dotenv(dotenv_path="../data/.env")
   # Dict for return values
   global env
   env = {}

   # Take the environment variable, default to false
   # If the variable is "True", then True
   env['useREST'] = getenv("IG2USEREST", 'False') == 'True'
   # Take the environment variable, default to None
   env['useGPU'] = getenv("IG2USEGPU", None)
   if env['useGPU'] == "False":
      env['useGPU'] = False
   elif env['useGPU'] == "True":
      env['useGPU'] = True

   env['downloadMethod'] = getenv("IG2DLMETHOD", stanza.DownloadMethod.DOWNLOAD_RESOURCES)
   if env['downloadMethod'] == "reuse":
      env['downloadMethod'] = stanza.DownloadMethod.REUSE_RESOURCES
   elif env['downloadMethod'] == "none":
      env['downloadMethod'] = stanza.DownloadMethod.NONE

   env['logLevel'] = getenv("IG2STANZALOGLEVEL")

   env['displacyPort'] = int(getenv("IG2DISPLACYPORT", 5001))

   env['flaskURL'] = getenv("IG2FLASKURL", "http://localhost:5000")

   logLevels = {"INFO":logging.INFO,
               "DEBUG":logging.DEBUG,
               "WARN":logging.WARNING,
               "ERROR":logging.ERROR,
               "CRITICAL":logging.CRITICAL,
               }

   env["logLevelFile"] = getenv("IG2LOGLEVELFILE")
   if env["logLevelFile"] in logLevels.keys():
      env["logLevelFile"] = logLevels[env["logLevelFile"]]
   else:
      env["logLevelFile"] = logging.DEBUG

   env["logLevelConsole"] = getenv("IG2LOGLEVELCONSOLE")
   if env["logLevelConsole"] in logLevels.keys():
      env["logLevelConsole"] = logLevels[env["logLevelConsole"]]
   else:
      env["logLevelConsole"] = logging.DEBUG

   return env

def createLogger():
   """Creates a custom logger instance shared with all programs importing this file"""

   global logger

   logger = logging.getLogger(__name__)

   # Accept all logs
   logger.setLevel(logging.DEBUG)

   # Handlers for console and file output with separate logging levels
   fileHandler = logging.FileHandler("..\data\logs\log.log")
   consoleHandler = logging.StreamHandler()
   fileHandler.setLevel(env["logLevelFile"])
   consoleHandler.setLevel(env["logLevelConsole"])

   # Custom formatting for console and file output
   formatterFile = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',
                              '%d/%m/%Y %I:%M:%S %p')
   formatterConsole = logging.Formatter('%(levelname)s: %(message)s')
   consoleHandler.setFormatter(formatterConsole)
   fileHandler.setFormatter(formatterFile)

   # Add the custom handlers to the logger
   logger.addHandler(fileHandler)
   logger.addHandler(consoleHandler)

loadEnvironmentVariables()
createLogger()