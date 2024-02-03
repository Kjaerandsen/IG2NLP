import stanza
import time
#import copy

# Dictionary of symbols for parsing
SymbolDict = {"iobj":"Bind","obj":"Bdir","aux":"D", "aux:pass":"D","nsubj":"A"}

CombineObjandSingleWordProperty = True

nlp = None

# Word for handling words,
# takes the variables from the nlp pipeline output, and additional variables for handling components
class Word:
    def __init__(self, text, pos, deprel, head, id, lemma, xpos, 
                 start=0, end=0, spaces=0, symbol="", nested = False, position = 0):
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
        return("Word: "+ self.text + " pos: "+ self.pos + " deprel: "+ str(self.deprel) 
               + " head: " + str(self.head) + " id: " + str(self.id)
               + " start: " + str(self.start) + " end: " + str(self.end))

# MiddleWare for the matcher, initializes the nlp pipeline globally to reuse the pipeline across the
# statements and runs through all included statements.
def MatcherMiddleware(jsonData):
    global nlp
    nlp = stanza.Pipeline('en', use_gpu=False, download_method=None)
    #print(nlp.processors["sentiment"])
    nlp.processors.pop("sentiment")
    nlp.processors.pop("constituency")

    i = 0
    while i < len(jsonData): 
        base = jsonData[i]['baseTx']
        output = Matcher(base)

        print("\n"+ base + "\n" + jsonData[i]['manual'] + "\n" + output)

        jsonData[i]["stanza"] = output

        i += 1

    return jsonData

def Matcher(text):
    return WordsToSentence2(matchingFunction(compoundWordsMiddleware(nlpPipeline(text))))

# Takes a sentence as a string, returns the nlp pipeline results for the string
def nlpPipeline(text):
    # Run the nlp pipeline on the input text
    doc = nlp(text)
    return doc.sentences[0].words

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
                words[i].start_char,
                words[i].end_char,
                spaces
            ))
        
        #print(customWords[i])
        #print(words[i])

        i += 1

    return customWords

def compoundWordsMiddleware(words):
    customWords = convertWordFormat(words)

    customWords = compoundWords(customWords)
    customWords = compoundWords(customWords)

    return customWords

# Takes the words from the nlp pipeline and combines combine words to a single word
# Also converts the datatype to the Word class
def compoundWords(customWords):
    
    wordLen = len(customWords)
    '''
    i = 0
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
                words[i].start_char,
                words[i].end_char,
                spaces
            ))
        
        #print(customWords[i])
        #print(words[i])

        i += 1
    '''
    i = 0
    #print("type is: ", type(words[0]), " " , wordLen)
    while i < wordLen:
        #print(words[i])

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
            if customWords[i+2].deprel == "punct" and customWords[i+2].head-1 == i+1:
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

# Matching function, takes a list of words with dependency parse and pos-tag data.
# Returns a list of words with IG Script notation symbols.
def matchingFunction(words):
    wordLen = len(words)

    words2 = []

    i = 0

    while i < wordLen:
        deprel = words[i].deprel

        # For more complex dependencies
        if ":" in deprel:
            if deprel != "aux:pass" and deprel != "obl:tmod":
                print("\n", '":" dependency: ',words[i], "\n")

        #print(words[words[i].head-1], words[i].deprel, words[i].text)

        # If the word is recognized as a condition or constraint
        if words[i].deprel == "advcl":
            # Find the substructure for the condition or constraint
            # print("Advcl")

            firstVal = 0
            firstValFilled = False

            k = 0

            # Go through the statement from the first word to the advcl deprel
            while k < i:
                x = k
                headRel = ""
                while headRel != "root":
                    # Set x to the head of x
                    x = words[x].head-1
                    #print(words[x].deprel, words[x].text)
                    if words[x].deprel == "advcl":
                        if not firstValFilled:
                            firstVal = k
                            firstValFilled = True
                        headRel = "root"
                    headRel = words[x].deprel
                k += 1
            
            lastIndex = 0

            k = i+1
            while k < len(words):
                x = k
                headRel = ""
                while headRel != "root":
                    x = words[x].head-1
                    if words[x].deprel == "advcl":
                        lastIndex = k+1
                        headRel = "root"
                    headRel = words[x].deprel
                k += 1

            # Return the combination of the activation condition and the rest of the sentence
            if lastIndex < len(words) and words[lastIndex].deprel == "punct":

                if firstVal == 0:
                    contents = []

                    activationCondition = matchingFunction(
                        compoundWordsMiddleware(nlpPipeline(WordsToSentence(words[:lastIndex]))))
                    #actiWords = copy.deepcopy(words[:lastIndex])
                    #activationCondition = matchingFunction(reusePart(actiWords, 0, lastIndex))

                    if validateNested(activationCondition):
                        words2.append(Word(
                        "","","",0,0,"","",0,0,0,"Cac",True,1
                        ))
                        words2 += activationCondition
                        words2.append(Word("","","",0,0,"","",0,0,0,"Cac",True,2))
                        words2.append(words[lastIndex])
                    else:
                        words2 += words[:lastIndex]
                        words2[0].setSymbol("Cac",1)
                        words2[lastIndex-1].setSymbol("Cac",2)
                        words2.append(words[lastIndex])

                    #contents = matchingFunction(compoundWordsMiddleware(nlpPipeline(
                    #    WordsToSentence(words[lastIndex+1:]))))
                    contents = matchingFunction(reusePart(words[lastIndex+1:], lastIndex+1, 
                                                            wordLen-(lastIndex+1)))

                    # Copy over the old placement information to the 
                    # newly generated words for proper formatting
                    k = lastIndex +1
                    while k < len(words):
                        index = k-lastIndex-1
                        contents[index].id = words[k].id
                        contents[index].start = words[k].start
                        contents[index].end = words[k].end
                        contents[index].spaces = words[k].spaces

                        k += 1

                    # print("Contents are: '", contents[0].text, "'")
                    words2 += contents

                    return words2

        # Cex detection
        if deprel == "obl":
            # Check for connections to the obl both before and after
            scopeStart = i
            scopeEnd = i

            j = 0
            while j < wordLen:
                if words[j].head-1 == i and words[j].deprel != "punct":
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                #elif words[words[j].head-1].head-1 == i and words[j].deprel != "punct":
                #    if j > scopeEnd:
                #        scopeEnd = j
                #    elif j < scopeStart:
                #        scopeStart = j
                elif ifHeadRelation(words, j, i) and words[j].deprel != "punct":
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                j += 1
            
            if scopeEnd - scopeStart != 0:
                # Look for symbols within
                '''
                j = scopeStart
                while j < scopeEnd:
                    if words[j].symbol != "":
                        print("\n\nNot none\n\n", words[j].symbol)
                    j += 1
                '''
                # Add the words as a Cex
                words[scopeStart].setSymbol("Cex", 1)
                words[scopeEnd].setSymbol("Cex", 2)
            
            i = scopeEnd
    
        # Cex detection 2
        elif deprel == "obl:tmod":
            i = words[i].head-1

            scopeStart = i
            scopeEnd = i

            j = 0

            while j < wordLen:
                if (words[j].head-1 == i 
                    and words[j].deprel != "punct" 
                    and words[j].deprel != "cc"):
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                elif (ifHeadRelation(words, j, i) 
                      and words[j].deprel != "punct"
                      and words[j].deprel != "cc"):
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                j += 1
            
            if scopeEnd - scopeStart != 0:
                # Add the words as a Cex
                words[scopeStart].setSymbol("Cex", 1)
                words[scopeEnd].setSymbol("Cex", 2)
            
            i = scopeEnd

        # Object detection
        elif deprel == "obj" :
            iBak = i
            smallLogicalOperator(words, i, "Bdir", wordLen)
            # If the flag is True combine the object with single word properties preceeding 
            # the object
            if CombineObjandSingleWordProperty:
                if (words[iBak-1].symbol == "Bdir,p" and words[iBak-1].deprel == "amod"
                    and words[iBak-1].position == 0):
                    if iBak != i:
                        words[iBak].setSymbol("", 0)
                        words[iBak-1].setSymbol("Bdir", 1)
                    else:
                        words[iBak].setSymbol("Bdir", 2)
                        words[iBak-1].setSymbol("Bdir", 1)

        # Aim detection
        elif deprel == "root":
            # Look for logical operators
            if not smallLogicalOperator2(words, i, "I", wordLen):
                words[i].setSymbol("I")
                
                # Look for xcomp dependencies
                k = 0

                while k < wordLen:
                    if words[k].deprel == "xcomp" and words[k].head-1 == i:
                        print("XComp of I: ", words[k], k, i)
                        if k-i == 2:
                            words[i].setSymbol("I",1)
                            words[i+2].setSymbol("I",2)
                    k += 1
            
        
        # Else if the word has an amod dependency type, check if the head is a symbol
        # that supports properties, if so, the word is a property of that symbol
        elif words[i].deprel == "amod":
            # If the word is directly connected to an obj (Bdir)
            if words[words[i].head-1].deprel == "obj":
                smallLogicalOperator(words, i, "Bdir,p", wordLen)
                #words[i].setSymbol("Bdir,p")
            # Else if the word is directly connected to an iobj (Bind)
            elif words[words[i].head-1].deprel == "iobj":
                smallLogicalOperator(words, i, "Bind,p", wordLen)
                #words[i].setSymbol("Bind,p")
            # Else if the word is connected to a nsubj connected directly to root (Attribute)
            elif (words[words[i].head-1].deprel == "nsubj" 
                  and words[words[words[i].head-1].head-1].deprel == "root"):
                smallLogicalOperator(words, i, "A,p", wordLen)
                #words[i].setSymbol("A,p")

        elif words[i].deprel == "nmod:poss":
            if words[words[i].head-1].deprel == "obj" and words[i].head-1 == i+1:
                # Check if there is a previous amod connection and add both
                if words[i-1].deprel == "amod" and words[i-1].head-1 == i:
                    words[i-1].setSymbol("Bdir,p", 1)
                    words[i].setSymbol("Bdir,p", 2)
                # Else only add the Bdir,p
                else:
                    words[i].setSymbol("Bdir,p")
            else:
                print("\nWord is nmod:poss: ", words[i])
        
        # Too broad coverage in this case, detected instances which should be included in the main
        # object in some instances, an instance of an indirect object component, and several 
        # overlaps with execution constraints.
        #elif words[i].deprel == "nmod" and words[words[i].head-1].deprel == "obj":
        #    words[i].setSymbol("Bdir,p")

        # If the head of the word is the root, check the symbol dictionary for symbol matches
        elif words[words[i].head-1].deprel == "root":
            if words[i].deprel in SymbolDict:
                words[i].setSymbol(SymbolDict[words[i].deprel])
        
        # If the relation is a ccomp then handle it as a direct object
                '''
        elif (words[i].deprel == "amod" 
              and words[words[i].head-1].deprel == "nsubj" 
              and words[words[words[i].head-1].head-1].deprel == "ccomp"):
            #print("\n\nAMOD NSUBJ OBJ\n\n")
            words[i].setSymbol(words[i],"bdir", 1)
            words[i+1].setSymbol(words[i+1],"bdir", 2)
            i += 1
            '''
        elif words[i].deprel == "nsubj" and words[words[i].head-1].deprel == "ccomp":
            print("\n\nNSUBJ CCOMP OBJ\n\n")
        
        i += 1

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

# Reconstructs the base statement from the words maintaining original spacing.
def WordsToSentence(words):
    wordLen = len(words)
    index = 0
    i = 0

    sentence = ""

    while i < wordLen:
        if words[i].start > index:
            sentence += " "*(words[i].start-index) + words[i].text
            index += 1 + len(words[i].text)
        elif words[i].start <= index:
            sentence += words[i].text
            index = len(sentence)
        i += 1

    return sentence

# Builds the final annotated statement.
def WordsToSentence2(words):
    i = 0

    sentence = ""

    while i < len(words):
        sentence += words[i].buildString()
        i += 1
    
    return sentence

# Validation function for nested components
# Sets a requirement of both an Aim and an Attribute detected for a component to 
# be regarded as nested.
def validateNested(words):
    wordLen = len(words)

    Aim = False
    Attribute = False

    i = 0
    while i < wordLen:
        if words[i].symbol == "A":
            Attribute = True
            if Aim:
                return True
        if words[i].symbol == "I":
            Aim = True
            if Attribute:
                return True
        i += 1
    return False

# Check if the word is connected to the headId through a head connection
def ifHeadRelation(words, wordId, headId):
    while words[words[wordId].head-1].deprel != "root":
        if words[wordId].deprel == "root":
            return False
        if words[wordId].head-1 == headId:
            return True
        wordId = words[wordId].head-1
    return False

# Finds and handles symbols with logical operators
def smallLogicalOperator(words, i, symbol, wordLen):
    # If there is a logical operator adjacent        
    scopeStart = i  
    scopeEnd = i

    j=0
    cc = False
    while j < wordLen:
        if words[j].deprel == "cc":
            if words[words[j].head-1].head-1 == i:
                cc = True
                if j > scopeEnd:
                    scopeEnd = j
                elif j < scopeStart:
                    scopeStart = j
        elif words[j].deprel == "conj":
            if words[j].head-1 == i:
                if j > scopeEnd:
                    scopeEnd = j
                elif j < scopeStart:
                    scopeStart = j
        j += 1
            
    if scopeEnd - scopeStart != 0 and cc:
        outOfScope = False
        j = scopeStart
        while j < scopeEnd:
            if (j!=i and words[j].deprel != "conj" 
                         and words[j].deprel != "punct" and words[j].deprel != "cc"):
                outOfScope = True
                break
            j += 1

        if not outOfScope:
            j = scopeStart
            while j < scopeEnd:
                if words[j].deprel == "cc":
                    words[j].text = "["+ words[j].text.upper()+"]"
                j += 1
            words[scopeStart].setSymbol(symbol, 1)
            words[scopeEnd].setSymbol(symbol, 2)
            i = scopeEnd
        else:
            words[i].setSymbol(symbol)
    else:
        words[i].setSymbol(symbol)

# Finds and handles symbols with logical operators
def smallLogicalOperator2(words, i, symbol, wordLen):
    # If there is a logical operator adjacent        
    scopeStart = i  
    scopeEnd = i

    j=0
    cc = False
    while j < wordLen:
        if words[j].deprel == "cc":
            if words[words[j].head-1].head-1 == i:
                cc = True
                if j > scopeEnd:
                    scopeEnd = j
                elif j < scopeStart:
                    scopeStart = j
        elif words[j].deprel == "conj":
            if words[j].head-1 == i:
                if j > scopeEnd:
                    scopeEnd = j
                elif j < scopeStart:
                    scopeStart = j
        j += 1
            
    if scopeEnd - scopeStart != 0 and cc:
        outOfScope = False
        j = scopeStart
        while j < scopeEnd:
            if (j!=i and words[j].deprel != "conj" 
                         and words[j].deprel != "punct" and words[j].deprel != "cc"):
                outOfScope = True
                break
            j += 1

        if not outOfScope:
            j = scopeStart
            while j < scopeEnd:
                if words[j].deprel == "cc":
                    words[j].text = "["+ words[j].text.upper()+"]"
                j += 1
            words[scopeStart].setSymbol(symbol, 1)
            words[scopeEnd].setSymbol(symbol, 2)
            i = scopeEnd
            return True
        else:
            return False
    else:
        return False

# Function that tries to use the old dependency parse tree for the second part of sentences starting
# with an activation condition. If the words do not include a root connection the words are
# parsed again.
def removeStart(words, offset, wordLen):
    i = 0

    noRoot = True
    while i < wordLen:
        #print(words[i])
        if words[i].head != 0:
            words[i].head -= offset
        if words[i].deprel == "root":
            noRoot = False
        words[i].id -= offset
        #print(words[i].id, words[i].head)

        i+=1

    if noRoot:
        return compoundWordsMiddleware(nlpPipeline(WordsToSentence(words)))

    return words

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
            #print(words[i])
            if words[i].head != 0:
                words[i].head -= offset
                if words[i].head < 0:
                    words[i].deprel = "root"
            words[i].id -= offset
            #print(words[i].id, words[i].head)
            #print(words[i])
            i+=1

    return words