from os import getenv
from dotenv import load_dotenv
from stanza import DownloadMethod
import logging

# Word for handling words,
# takes the variables from the nlp pipeline output, and additional variables for handling components
class Word:
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

    # Returns the contents as a string, maintaining the source formatting in empty preceeding spaces
    def getContents(self):
        output = self.buildString
        if self.spaces > 0:
            return " " * self.spaces + output
        else:
            return output
        
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
    def setHead(self, head):
        self.head = head-1

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

            j=0
            while j < tokenSize:
                word = words[i]

                startLoc = tokenText.find(word.text)

                spaces = startLoc
                startChar = endChar + spaces
                endChar = startChar + len(word.text)

                wordText = tokenText[startChar:endChar]
                tokenText = tokenText[endChar:]
                
                addToCustomWords(customWords,words[i], wordText, startChar,endChar,spaces)
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
            customWords[i].scope = scope
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
    customWords = convertWordFormat(words)

    customWords = compoundWords(customWords)
    customWords = compoundWords(customWords)

    return customWords

def compoundWordsMiddlewareWords(words):
    words = compoundWords(words)
    words = compoundWords(words)

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

# Takes a list of words, an id, the length of the list of words and a direction
# Combines the word with the next (0) or 
# previous (1) word and removes the extra word from the list of words
def removeWord(words,i,wordLen,direction=0):
    if direction == 0:
        id = i+1
        words[id].combineWords(words[i], False)
    else:
        id = i
        words[id-1].combineWords(words[i], True)

    # Go through the words and adjust the connections between the words to account
    # for the combination of compound words into single words
    j = 0
    while j < wordLen:
        # Adjust the head connections to take into account the compounding of two elements
        if words[j].head > id:
            words[j].head = words[j].head - 1
        # Adjust the id's to take into account the removal of the compound word
        if j >= i:
            words[j].id -=  1
        j += 1

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
    #print(WordsToSentence(words))

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

    while i < len(words):
        sentence += words[i].buildString()
        i += 1
    
    return sentence

# Function that takes a list of words and tries to reuse the list for further matching by
# updating the root of this subset of words.
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

# Function that loads all environment variable from ".env" file or environment
def loadEnvironmentVariables():
    load_dotenv()

    # Dict for return values
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

    env['downloadMethod'] = getenv("IG2DLMETHOD", DownloadMethod.DOWNLOAD_RESOURCES)
    if env['downloadMethod'] == "reuse":
        env['downloadMethod'] = DownloadMethod.REUSE_RESOURCES
    elif env['downloadMethod'] == "none":
        env['downloadMethod'] = DownloadMethod.NONE

    env['logLevel'] = getenv("IG2STANZALOGLEVEL")

    env['displacyPort'] = int(getenv("IG2DISPLACYPORT", 5001))

    env['flaskURL'] = getenv("IG2FLASKURL", "http://localhost:5000")

    logLevels = {"INFO":logging.INFO,
                 "DEBUG":logging.DEBUG,
                 "WARN":logging.WARNING,
                 "ERROR":logging.ERROR,
                 "CRITICAL":logging.CRITICAL,
                 }
    env['logLevelFile'] = getenv("IG2LOGLEVELFILE")
    print(env['logLevelFile'], logLevels.keys())
    if env['logLevelFile'] in logLevels.keys():
        print("YES")
        env['logLevelFile'] = logLevels[env['logLevelFile']]
    else:
        env['logLevelFile'] = logging.DEBUG
    
    env['logLevelConsole'] = getenv("IG2LOGLEVELCONSOLE")
    if env['logLevelConsole'] in logLevels.keys():
        env['logLevelConsole'] = logLevels[env['logLevelConsole']]
    else:
        env['logLevelConsole'] = logging.DEBUG

    print(env["logLevelFile"])
    return env