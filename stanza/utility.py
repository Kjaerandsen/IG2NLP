# Word for handling words,
# takes the variables from the nlp pipeline output, and additional variables for handling components
class Word:
    def __init__(self, text, pos, deprel, head, id, lemma, xpos, feats,
                 start=0, end=0, spaces=0, symbol="", nested = False, position = 0, ner=""):
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
        if i > 0:
            spaces = words[i].start_char - words[i-1].end_char
        else:
            spaces = 0

        customWords.append(
            Word(
                words[i].text,
                words[i].pos,
                words[i].deprel,
                words[i].head,
                words[i].id,
                words[i].lemma,
                words[i].xpos,
                words[i].feats,
                words[i].start_char,
                words[i].end_char,
                spaces
            ))

        i += 1

    return customWords

# Middleware function for compounding words (multi-word expressions) into single words
# Converts the word datatype to the custom class and runs the compoundWords function twice
def compoundWordsMiddleware(words):
    customWords = convertWordFormat(words)

    customWords = compoundWords(customWords)
    customWords = compoundWords(customWords)

    return customWords

def compoundWordsMiddlewareAdvanced(words, tokens):
    #customWords = convertWordFormatAdvanced(words, tokens)

    customWords = compoundWords(customWords)
    customWords = compoundWords(customWords)

    return customWords

# Takes the words from the nlp pipeline and combines combine words to a single word
# Also converts the datatype to the Word class
def compoundWords(customWords):
    
    wordLen = len(customWords)
    i = 0
    #print("type is: ", type(words[0]), " " , wordLen)
    while i < wordLen:
        # Compound of three words in the form compound, punct, word
        # Combines the punct and the compound first, then the main function combines the rest
        # the compound and the word
        if customWords[i].deprel == "compound" and abs(customWords[i].head-1 - i) == 2:
            if i < customWords[i].head-1:
                if customWords[i+1].deprel == "punct":
                    i, wordLen = removeWord(customWords, i+1, wordLen, 1)
                    i-=1

        # If the word is a compound word
        elif customWords[i].deprel == "compound" and customWords[i].head-1 == i+1: 
            i, wordLen = removeWord(customWords, i, wordLen)

        
        elif (customWords[i].deprel == "case" and customWords[i].head-1 == i-1 
              and customWords[i].pos == "PART"):
            # Add the PART case (i.e with "state" and "'s" -> "state's")
            #customWords[i-1].text = customWords[i-1].text + customWords[i].text
            i, wordLen = removeWord(customWords, i, wordLen, 1)

        
        # If the word is a "PART" case dependency
        elif customWords[i].deprel == "punct" and customWords[i].head-1 == i+1:
            if (i+2 < wordLen and customWords[i+2].deprel == "punct" and 
                customWords[i+2].head-1 == i+1):
                # Combine the punct and following word
                i, wordLen = removeWord(customWords, i, wordLen)

        # If the word is a compound part of the previous word, combine the previous and the current
        elif customWords[i].deprel == "compound:prt" and customWords[i].head-1 == i-1:
            i, wordLen = removeWord(customWords, i, wordLen, 1)
        i += 1

    return customWords

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