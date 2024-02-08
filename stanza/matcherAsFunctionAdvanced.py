import stanza
import time
import copy

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1

# Global variable for the nlp pipeline, allows for reusing the pipeline 
# without multiple initializations
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
        print("\nStatement", str(i) + ": " + jsonData[i]['name'])
        print(base + "\n" + jsonData[i]['manual'] + "\n" + output)
        
        jsonData[i]["stanza"] = output
        i += 1

    return jsonData

# Matcher function
# Performs all steps for automatically annotating a sentence, from running the pipeline on the text
# to handling the data, matching the dependencies to components and writing the final string.
def Matcher(text):
    return WordsToSentence(matchingFunction(compoundWordsMiddleware(nlpPipeline(text))))

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

        i += 1

    return customWords

# Middleware function for compounding words (multi-word expressions) into single words
# Converts the word datatype to the custom class and runs the compoundWords function twice
def compoundWordsMiddleware(words):
    customWords = convertWordFormat(words)

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
    wordsBak = copy.deepcopy(words)
    i = 0

    while i < wordLen:
        deprel = words[i].deprel

        # Print out more complex dependencies for future handling
        if ":" in deprel:
            if deprel != "aux:pass" and deprel != "obl:tmod":
                print("\n", '":" dependency: ',words[i], "\n")

        #print(words[words[i].head-1], words[i].deprel, words[i].text)

        # (Cac, Cex) Condition detection 
        if deprel == "advcl":
            words2 = []
            if handleCondition(words, wordsBak, i, wordLen, words2):
                return words2

        # (O) Or else detection
        elif deprel == "cc" and words[i+1].text == "else":
            words2 = []
            orElseHandler(words, wordsBak, wordLen, words2, i)
            return words2

        # (Cex) Execution constraint detection
        elif deprel == "obl":
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
            
            if scopeEnd - scopeStart >= minimumCexLength:
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

        # Advmod of Aim is correlated with execution constraints
        # Might be too generic of a rule.
        elif deprel == "advmod" and words[words[i].head-1].symbol == "I":
            #print("\nadvmod connected to Aim(I): ", words[i])
            if i+1 < wordLen:
                if words[i+1].deprel == "punct":
                    words[i].setSymbol("Cex")

        # (Cex) Execution constraint detection 2
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

        elif deprel == "nmod" and words[words[i].head-1].symbol == "A":
            print("\nnmod connected to Attribute(A): ", words[i])

        # (Bdir) Object detection
        elif deprel == "obj":
            iBak = i
            smallLogicalOperator(words, i, "Bdir", wordLen)
            # Positive lookahead for nmod to include:
            # May need future refinement
            if words[i].position == 0:
                j=i
                while j < wordLen:
                    if words[j].deprel == "nmod" and words[j].head-1 == i:
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

        # (Bind) Indirect object detection
        elif deprel == "iobj":
            iBak = i
            smallLogicalOperator(words, i, "Bind", wordLen)
            # If the flag is True combine the object with single word properties preceeding 
            # the object

            if CombineObjandSingleWordProperty:
                if (words[iBak-1].symbol == "Bind,p" and words[iBak-1].deprel == "amod"
                    and words[iBak-1].position == 0):
                    if iBak != i:
                        words[iBak].setSymbol("", 0)
                        words[iBak-1].setSymbol("Bind", 1)
                    else:
                        words[iBak].setSymbol("Bind", 2)
                        words[iBak-1].setSymbol("Bind", 1)


        # (I) Aim detection
        elif deprel == "root":
            # Potentially unmatch all occurences where the aim is not a verb
            #if words[i].pos != "VERB":
            #    print("Aim is not VERB:", words[i].pos, words[i])
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
                            break
                        else:
                            j = i+1
                            while j < k-1:
                                if words[j].head-1 != k:
                                    words[i].text = (words[i].text + " " * words[k].spaces + "[" + 
                                                     words[k].text + "]")
                                    words[i].setSymbol("I")
                                    j = k
                                    break
                                j+=1
                            if j == k-1:
                                words[i].setSymbol("I",1)
                                words[k].setSymbol("I",2)
                            
                        
                    k += 1
            
        
        # Else if the word has an amod dependency type, check if the head is a symbol
        # that supports properties, if so, the word is a property of that symbol
        # (Bdir,p, Bind,p, A,p)
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
                  and (words[words[words[i].head-1].head-1].deprel == "root" or 
                  words[words[words[i].head-1].head-1].symbol == "A")):
                smallLogicalOperator(words, i, "A,p", wordLen)
                #words[i].setSymbol("A,p")

        # (Bdir,p) Direct object property detection 2
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
        
        # (A) Attribute detection
        elif "nsubj" in deprel:
            if words[i].pos != "PRON":
                # Look for nmod connected to the word i
                j = 0

                other = False
                while j < wordLen:
                    if "nmod" in words[j].deprel and ifHeadRelation(words, j, i):
                        #print("Nmod head relation to a: ", words[j], words[i])
                        smallLogicalOperator(words, j, "A", wordLen)
                        other = True
                    j+=1 
                if not other:
                    smallLogicalOperator(words, i, "A", wordLen)
            # If the nsubj is a pronoun connected to root then handle it as an attribute
            # This may need to be reverted in the future if coreference resolution is used
            # in that case, the coreference resolution will be used to add the appropriate attribute
            elif words[words[i].head-1].deprel == "root":
                smallLogicalOperator(words, i, "A", wordLen)

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

        # Too broad coverage in this case, detected instances which should be included in the main
        # object in some instances, an instance of an indirect object component, and several 
        # overlaps with execution constraints.
        #elif words[i].deprel == "nmod" and words[words[i].head-1].deprel == "obj":
        #    words[i].setSymbol("Bdir,p")
                
        # (D) Deontic detection
        elif words[words[i].head-1].deprel == "root":
            if "aux" in deprel:
                if words[words[i].head-1].pos == "VERB":
                    # Combine two adjacent deontics if present.
                    if words[i-1].symbol == "D":
                        words[i-1].setSymbol("D",1)
                        words[i].setSymbol("D",2)
                    else:
                        if (words[i].head-1 - i) > 1:
                            words[i].setSymbol("D",1)
                            words[words[i].head-2].setSymbol("D",2)
                        else:
                            words[i].setSymbol("D")
                else:
                    print("Deontic, no verb")
        
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

# Builds the final annotated statement or reconstructs the base statement.
def WordsToSentence(words):
    i = 0

    sentence = ""

    while i < len(words):
        sentence += words[i].buildString()
        i += 1
    
    return sentence

# Validation function for nested components
# Sets a requirement of both an Aim (I) and an Attribute (A) detected for a component to 
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
    # Locations (ids) of cc dependent words
    ccLocs = []
    # Locations (ids) of puncts
    punctLocs = []
    # Locations (ids) of determiners
    detLocs = []

    # Go through the word list and find the scope of the component
    while j < wordLen:
        if words[j].deprel == "cc":
            if words[words[j].head-1].head-1 == i:
                ccLocs.append(j)
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
        # Also include advmod dependencies
        elif words[j].deprel == "advmod":
            if words[words[j].head-1].head-1 == i:
                if j > scopeEnd:
                    scopeEnd = j
                elif j < scopeStart:
                    scopeStart = j
        j += 1
        
    ccCount = len(ccLocs)

    # If the scope is larger than one word in length and there is a cc deprel in the scope (and/or)
    if scopeEnd - scopeStart != 0 and ccCount > 0:
        if ccCount == 1:
            outOfScope = False
            # Go through the scope, if a deprel other than conj, cc and det is found
            # then handle it as a single word component instead.
            j = scopeStart
            while j < scopeEnd:
                '''
                if (j!=i and words[j].deprel != "conj" 
                            and words[j].deprel != "punct" and words[j].deprel != "cc" 
                            and words[j].deprel != "det"):
                    print(words[j], words[j].pos, words[j].deprel)
                    #outOfScope = True
                    break
                '''
                if words[j].deprel == "det":
                    if j == scopeStart:
                        detLocs.append(j)
                    elif words[j-1].deprel == "cc":
                        detLocs.append(j)
                # Remove additional puncts (i.e. "x, and y" -> "x and y")
                elif words[j].deprel == "punct" and words[j].text == ",":
                    if words[j+1].deprel == "cc":
                        #if j+1 < scopeEnd:
                            words[j].spaces = 0
                            words[j].text = ""
                    # If the word is a punct connected to the conj, then it should be replaced by a
                            # logical operator
                    elif words[words[j].head-1].deprel == "conj":
                        punctLocs.append(j)
                j += 1

            if not outOfScope:
                # Set the contents of the cc to be a logical operator
                words[ccLocs[0]].text = "["+ words[ccLocs[0]].text.upper()+"]"

                j = 0
                while j < len(detLocs):
                    k = detLocs[j]
                    if k+1 < scopeEnd:
                        words[k+1].spaces = words[k].spaces
                        words[k].spaces = 0
                        words[k].text = ""
                    else:
                        words[k].spaces = 0
                        words[k].text = ""
                    j += 1

                # Turn all extra punct deprels into the same logical operator as above
                j = 0
                while j < len(punctLocs):
                    words[punctLocs[j]].spaces += 1
                    words[punctLocs[j]].text = words[ccLocs[0]].text
                    j+=1

                words[scopeStart].setSymbol(symbol, 1)
                words[scopeEnd].setSymbol(symbol, 2)
                i = scopeEnd
            else:
                print("Out of scope")
                words[i].setSymbol(symbol)
        else:
            print("More than one CC")
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
        if words[i].head != 0:
            words[i].head -= offset
        if words[i].deprel == "root":
            noRoot = False

        words[i].id -= offset
        i+=1

    if noRoot:
        return compoundWordsMiddleware(nlpPipeline(WordsToSentence(words)))

    return words

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

# Handler function for the matching and encapsulation of conditions (Cac, Cex)
def handleCondition(words, wordsBak, i, wordLen, words2):
    firstVal = i
    
    # Go through the statement until the word is connected to the advcl directly or indirectly
    k = 0
    while k < i:
        # If connected to the advcl then set firstVal to the id and break the loop
        if ifHeadRelation(words, k, i):
            firstVal = k
            break
        k += 1

    # Go through again from the activation condition++
    # Until the word is no longer connected to the advcl
        
    # Set the lastVal to the current id -1
            
    lastIndex = 0
    k = i+1
    while k < len(words):
        if not ifHeadRelation(words, k, i):
            lastIndex = k-1
            break
        k += 1

    if words[lastIndex].deprel != "punct":
        if words[lastIndex+1].deprel == "punct":
            lastIndex += 1
        else:
            #print("Last val was not punct", words[lastIndex])
            return False

    if firstVal == 0:
        contents = []

        activationCondition = matchingFunction(
            compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[:lastIndex]))))
        #actiWords = copy.deepcopy(words[:lastIndex])
        #activationCondition = matchingFunction(reusePart(actiWords, 0, lastIndex))

        j = 0
        oblCount = 0
        while j < len(activationCondition):
            if "obl" in activationCondition[j].deprel:
                oblCount+=1
            j+=1

        if oblCount > 1 and words[0].deprel == "mark":
            symbol = "Cex"
        else:
            symbol = "Cac"

        if validateNested(activationCondition):
            words2.append(Word(
            "","","",0,0,"","",0,0,0,symbol,True,1
            ))
            words2 += activationCondition
            words2.append(Word("","","",0,0,"","",0,0,0,symbol,True,2))
            words2.append(words[lastIndex])
        else:
            words2 += words[:lastIndex]
            words2[0].setSymbol(symbol,1)
            words2[lastIndex-1].setSymbol(symbol,2)
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

        return True
    elif words[firstVal].deprel == "mark":
        #print("First val was not id 0 and deprel was mark", words[lastIndex])
        # Do the same as above, but also with the words before this advcl
        contents = []

        preActivationCondition = matchingFunction(
            compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[:firstVal]))))
        words2 += preActivationCondition

        activationCondition = matchingFunction(
            compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[firstVal:lastIndex]))))
        
        #actiWords = copy.deepcopy(words[:lastIndex])
        #activationCondition = matchingFunction(reusePart(actiWords, 0, lastIndex))
        j = 0
        oblCount = 0
        while j < len(activationCondition):
            if "obl" in activationCondition[j].deprel:
                oblCount+=1
            j+=1

        if oblCount > 1:
            symbol = "Cex"
        else:
            symbol = "Cac"

        if validateNested(activationCondition):
            words2.append(Word(
            "","","",0,0,"","",0,0,1,symbol,True,1
            ))
            words2 += activationCondition
            words2.append(Word("","","",0,0,"","",0,0,0,symbol,True,2))
            words2.append(words[lastIndex])
        else:
            words2 += wordsBak[firstVal:lastIndex]
            words2[firstVal].setSymbol(symbol,1)
            words2[lastIndex-1].setSymbol(symbol,2)
            words2.append(words[lastIndex])

        #contents = matchingFunction(compoundWordsMiddleware(nlpPipeline(
        #    WordsToSentence(words[lastIndex+1:]))))
        #contents = matchingFunction(reusePart(words[lastIndex+1:], lastIndex+1, 
        #                                            wordLen-(lastIndex+1)))
        
        if len(wordsBak) > lastIndex+1:
            contents = matchingFunction(
                compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[lastIndex+1:]))))

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

        return True
    else:
        #print("First val was not id 0 and deprel was not mark", words[lastIndex])
        return False

# Backup of the old activation condition handler
def handleActivationCondition2(words, wordsBak, i, wordLen, words2):
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
                compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[:lastIndex]))))
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

            return True
        else:
            return False
    return False

# Handler function for the Or else (O) component
def orElseHandler(words, wordsBak, wordLen, words2, firstVal):
    # Go through again from the activation condition++
    # Until the word is no longer connected to the advcl
        
    if words[wordLen-1].deprel == "punct":
        lastIndex = wordLen -1
    else:
        lastIndex = wordLen

    contents = []

    words2 += matchingFunction(
        compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[:firstVal]))))

    print(WordsToSentence(wordsBak[firstVal+2:lastIndex]))
    activationCondition = matchingFunction(
        compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[firstVal+2:lastIndex]))))
    #actiWords = copy.deepcopy(words[:lastIndex])
    #activationCondition = matchingFunction(reusePart(actiWords, 0, lastIndex))

    words2.append(Word(
    "","","",0,0,"","",0,0,1,"O",True,1
    ))
    words2 += activationCondition
    words2.append(Word("","","",0,0,"","",0,0,0,"O",True,2))
    if words[wordLen-1].deprel == "punct":
        words2.append(words[wordLen-1])