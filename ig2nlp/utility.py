from os import getenv
from dotenv import load_dotenv
import stanza
import logging

# Word for handling words,
# takes the variables from the nlp pipeline output, and additional variables for handling components
class Word:
    # Use slots for faster access
    # Limits variables of the class to only the defined attributes
    __slots__ = ("text", "pos", "deprel", "head", "id", "lemma", "xpos", "feats",
                 "start", "end", "spaces", "symbol", "nested", "position", "ner",
                 "logical", "corefid", "coref", "corefScope", "isRepresentative")

    def __init__(self, text, pos, deprel, head, id, lemma, xpos, feats,
                 start=0, end=0, spaces=0, symbol="", nested = False, position = 0, ner="", 
                 logical=0, corefid = -1, coref = "", corefScope = 0, isRepresentative=False):
        self.id = id
        self.text = text
        self.deprel = deprel
        self.head = head
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
        
    # Builds the contents as a component with brackets, the symbol and proper spacing in string form
    def buildString(self):
        output = " " * self.spaces
        if self.symbol != "":
            if self.nested:
                if self.position == 0:
                    output += self.symbol+"{"+self.text+"}"
                elif self.position == 1:
                    output += self.symbol + "{" + self.text
                elif self.position == 2:
                    output += self.text + "}"
            else:
                if self.position == 0:
                    output += self.symbol+"("+self.text+")"
                elif self.position == 1:
                    output += self.symbol + "(" + self.text
                elif self.position == 2:
                    output += self.text + ")"
        else:
            output += self.text
        return output
    
    def toLogical(self):
        if self.logical == 0:
            self.text = "[" + self.text.upper() + "]"
            self.logical = 4
    
    # Function to set the symbol of the word,
    # Position defines whether the symbol encapsulates only the word (0),
    # or if the word is the first word of the symbol(1), or the last(2).
    # Nested defines the nesting, if true use "{}" brackets, else use "()".
    def setSymbol(self, symbol, position=0, nested=False):
        self.symbol = symbol
        self.nested = nested
        self.position = position
    
    # Function for combining two subsequent words into one
    # Direction is a bool, True is left to right, False is right to left
    # The direction defines which start and end position to keep, and the text concatenation order
    def combineWords(self, otherWord, direction):
        if direction:
            self.end = otherWord.end
            self.text = self.text + " " * otherWord.spaces + otherWord.text
        else:
            self.start = otherWord.start
            self.text = otherWord.text + " " * self.spaces + self.text
            self.spaces = otherWord.spaces
    
    # Potential future adjustment as all head id's are one (1) to high.
    '''
    def setHead(self, head):
        self.head = head-1
    '''

    def __str__(self):
        return("Word: "+ self.text + " | pos: "+ self.pos + " | " + self.xpos  
               + " | deprel: "+ str(self.deprel) + " | id: " + str(self.id)
               + " | head: " + str(self.head) 
               + " | start: " + str(self.start) + " | end: " + str(self.end)
               + "\nLemma: " + self.lemma + " | Symbol: " + self.symbol + " "
               + str(self.position) + " " + str(self.nested) + " | NER:" + self.ner 
               + "\nFeats: " + self.feats)

def convertWordFormat(words):
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
            #    print(mention.__dict__.keys())
            #    print(mention.__dict__)

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
def addToCustomWords(customWords, word, text, start, end, spaces):
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
def compoundWordsMiddleware(words):
    words = convertWordFormat(words)

    words = compoundWords(words)
    words = compoundWords(words)
    # For compound (punct or cc) conj x relations, where one or more of the same cc are present
    words = compoundWordsConj(words)

    return words

def compoundWordsMiddlewareWords(words):
    words = compoundWords(words)
    words = compoundWords(words)
    # For compound (punct or cc) conj x relations, where one or more of the same cc are present
    words = compoundWordsConj(words)

    return words

# Takes the words from the nlp pipeline and combines combine words to a single word
# Also converts the datatype to the Word class
def compoundWords(words):
    
    wordLen = len(words)
    i = 0
    #print("type is: ", type(words[0]), " " , wordLen)
    while i < wordLen:
        # Compound of three words in the form compound, punct, word
        # Combines the punct and the compound first, then the main function combines the rest
        # the compound and the word
        if words[i].deprel == "compound" and abs(words[i].head-1 - i) == 2:
            if i < words[i].head-1:
                if words[i+1].deprel == "punct":
                    i, wordLen = removeWord(words, i+1, wordLen, 1)
                    i-=1

        # If the word is a compound word
        elif words[i].deprel == "compound" and words[i].head-1 == i+1: 
            i, wordLen = removeWord(words, i, wordLen)

        
        elif (words[i].deprel == "case" and words[i].head-1 == i-1 
              and words[i].pos == "PART"):
            # Add the PART case (i.e with "state" and "'s" -> "state's")
            #words[i-1].text = words[i-1].text + words[i].text
            i, wordLen = removeWord(words, i, wordLen, 1)

        
        # If the word is a "PART" case dependency
        elif words[i].deprel == "punct" and words[i].head-1 == i+1:
            if (i+2 < wordLen and words[i+2].deprel == "punct" and 
                words[i+2].head-1 == i+1):
                # Combine the punct and following word
                i, wordLen = removeWord(words, i, wordLen)

        # If the word is a compound part of the previous word, combine the previous and the current
        elif words[i].deprel == "compound:prt" and words[i].head-1 == i-1:
            i, wordLen = removeWord(words, i, wordLen, 1)
        i += 1

    return words

# Compound words handling for conj dependencies of the form compound cc conj root
def compoundWordsConj(words):
    wordLen = len(words)
    i = 0
    while i < wordLen:
        if words[i].deprel == "compound":
            i, _, wordLen = compoundWordsConjHelper(words, i, wordLen)
        i += 1
    return words

# Helper function performing the logic for compoundWordsConj
def compoundWordsConjHelper(words, i, wordLen):
    start = i
    end = words[i].head-1
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
        #        "compoundHandler did not detect a logical operator.")
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
        words[end].head = start+1
        words[end].deprel = "conj"
        # Every conj should have the first word as the head
        if len(conjLocs) > 1:
            for conjLoc in conjLocs[1:]:
                words[conjLoc].head = start+1
        
        for word in words:
            if word.head-1 == end:
                word.head = start+1

    return end, True, wordLen

# Takes a list of words, an id, the length of the list of words and a direction
# Combines the word with the next (0) or 
# previous (1) word and removes the extra word from the list of words
def removeWord(words,i,wordLen,direction=0):
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
        if word.head > id:
            word.head = word.head - 1
        # Adjust the id's to take into account the removal of the compound word
        if j >= i:
            word.id -=  1

    # Remove the extra word
    del words[i]
    return i-1, wordLen-1

def addWord(words, i, wordText):
    #print(i)
    for word in words:
        #print(word.head, word.head-1)
        if word.head-1 >= i and word.head != 0:
            word.head+=1
        
        if word.id > i:
            word.id += 1

    newWord = []
    newWord.append(Word(wordText,"","",0,i,"","","",0,0,words[i].spaces))
    #print(WordsToSentence(words[:i+1]))
    #print(WordsToSentence(newWord))
    #print(WordsToSentence(words[:i+1] + newWord + words[i+1:]))
    #print(WordsToSentence(words[:i+1] + words[i+1:]))
    #print(newWord[0].text)

    
    words = words[:i] + newWord + words[i:]

    return words


# Takes a list of tokens, returns the output text contained within.
def tokenToText(tokens):
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
def WordsToSentence(words):
    i = 0

    sentence = ""

    for word in words:
        sentence += word.buildString()
        i += 1
    
    return sentence

# Function that takes a list of words and tries to reuse the list for further matching by
# updating the root of this subset of words.
'''
def reusePart(words, offset, listLen):
    i = 0
    if offset == 0:
        rootId = 0
        while i < listLen:
            if words[i].head > listLen and words[i].deprel != "punct":
                words[i].deprel = "root"
                words[i].head = 0
                rootId = i
            elif words[i].deprel == "root":
                rootId = i

            i+=1

        i = 0
        while i < listLen:
            if words[i].head > listLen:
                words[i].head = rootId

            i+=1
    else:
        while i < listLen:
            if words[i].head != 0:
                words[i].head -= offset
                if words[i].head < 0:
                    words[i].deprel = "root"

            words[i].id -= offset
            i+=1

    return words
'''

# TODO: Add a check in reusePart functions for multiple "root" deprels
# Function that takes a list of words and tries to reuse the list for further matching by
# updating the root of this subset of words.
# For the End of Statement text
def reusePartEoS(words, firstVal):
    words[0].spaces = 0
    for word in words:
        if word.head-1 < firstVal:
            word.head = 0
            word.deprel = "root"
            logger.debug("Word outside of scope of reusePartEoS: " + word.text)
        else:
            word.head -= firstVal

    return words

# For the Start of Statement text
def reusePartSoS(words, lastVal):
    words[0].spaces = 0
    for word in words:
        if word.head-1 > lastVal:
            word.head = 0
            word.deprel = "root"
            logger.debug("Word outside of scope of reusePartSoS: " + word.text)

    return words

# For the Middle of a Statement text
def reusePartMoS(words, firstVal, lastVal):
    words[0].spaces = 1
    for word in words:
        if word.head-1 > lastVal or word.head-1 < firstVal:
            word.head = 0
            word.deprel = "root"
            logger.debug("Word outside of scope of reusePartMoS: " + word.text)
        else:
            word.head -= firstVal

    return words

# Function that loads all environment variable from ".env" file or environment
def loadEnvironmentVariables():
    load_dotenv()
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

# Create a custom logger instance shared with all programs importing this file
def createLogger():
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