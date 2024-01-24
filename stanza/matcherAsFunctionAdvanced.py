import stanza
import pandas as pd
from spacy import displacy

# Dictionary of symbols for parsing
SymbolDict = {"iobj":"Bind","obj":"Bdir","aux":"D","nsubj":"A"}

# Class for tokens or words in the text after going through the nlp pipeline and the matcher
# Has functionality for properly displaying the different words as strings for output formatting
class TokenEntry:
    def __init__(self, text, type, id=None, indexStart=None, indexEnd=None):
        self.id = id
        self.text = text
        self.type = type

    def __str__(self):
        #print(self.text, self.type)
        if self.id == None:
            return self.text
        elif self.type == "":
            return " " + self.text
        elif self.type == "punct":
            if self.text[0] == " " and len(self.text >= 1):
                self.text = self.text[1:]
                #print("Text is: ", self.text)
            return self.text
        else:
            return " " + self.type + "(" + self.text + ")"

# Word for handling   
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

    def getContents(self):
        output = self.buildString
        if self.spaces > 0:
            return " " * self.spaces + output
        else:
            return output
        
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
    def combineWords(self, otherWord, direction):
        if direction:
            self.end = otherWord.end
            self.text = self.text + " " * otherWord.spaces + otherWord.text
        else:
            self.start = otherWord.start
            self.text = otherWord.text + " " * self.spaces + self.text
            self.spaces = otherWord.spaces

    #def AppendStart(self, text):
    #    self.text = text + self.text
    #    self.end = self.start + len(self.text)
    
    def setHead(self, head):
        self.head = head-1

    def __str__(self):
        return("Word: "+ self.text + " pos: "+ self.pos + " deprel: "+ str(self.deprel) 
               + " head: " + str(self.head) + " id: " + str(self.id)
               + " start: " + str(self.start) + " end: " + str(self.end))

def Matcher(text):
    #print(WordsToSentence(compoundWords(nlpPipeline(text))))
    return WordsToSentence2(matchingFunction(compoundWords(nlpPipeline(text))))

# Takes a sentence as a string, returns the nlp pipeline results for the string
def nlpPipeline(text):
    nlp = stanza.Pipeline('en', use_gpu=False, download_method=None)

    # Take the input string
    doc = nlp(text)

    return doc.sentences[0].words

# Takes the words from the nlp pipeline and combines combine words to a single word
# Also converts the datatype to the Word class
def compoundWords(words):
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

    #print("type is: ", type(words[0]), " " , wordLen)
    while i < wordLen:
        #print(words[i])

        # If the word is a compound word
        if customWords[i].deprel == "compound" and customWords[i].head-1 == i+1: 
            #words[i+1].start_char = words[i].start_char
            # Set the text to the compound word and the following word
            
            #customWords[i+1].text = customWords[i].text + " " + customWords[i+1].text
            
            customWords[i+1].combineWords(customWords[i], False)

            # Go through the words and adjust the connections between the words to account
            # for the combination of compound words into single words
            j = 0
            while j < wordLen:
                # Adjust the head connections to take into account the compounding of two elements
                if customWords[j].head > i+1:
                    customWords[j].head = customWords[j].head - 1
                # Adjust the id's to take into account the removal of the compound word
                if j >= i:
                    customWords[j].id -=  1
                j += 1
            # Remove the old compound
            wordLen -= 1
            del customWords[i]
        
        # If the word is a "PART" case dependency
        elif customWords[i].deprel == "case" and customWords[i].head-1 == i-1 and customWords[i].pos == "PART":
            # Add the PART case (i.e with "state" and "'s" -> "state's")
            #customWords[i-1].text = customWords[i-1].text + customWords[i].text

            customWords[i-1].combineWords(customWords[i], True)
            
            # Go through the words and adjust the connections between the words to account
            # for the combination of compound words into single words
            j = 0
            while j < wordLen:
                # Adjust the head connections to take into account the compounding of two elements
                if customWords[j].head > i:
                    customWords[j].head = customWords[j].head-1
                # Adjust the id's to take into account the removal of the compound word
                if j >= i:
                    customWords[j].id -=  1
                j += 1

            # Remove the extra word
            wordLen -= 1
            del customWords[i]
            # Adjust i down as the current word is removed
            i-=1
        elif customWords[i].deprel == "punct" and customWords[i].head-1 == i+1:
            if customWords[i+2].deprel == "punct" and customWords[i+2].head-1 == i+1:
                # Combine the punct and following word
                #customWords[i+1].text = customWords[i].text+customWords[i+1].text
                customWords[i+1].combineWords(customWords[i], False)
                
                # Go through the words and adjust the connections between the words to account
                # for the combination of compound words into single words
                j = 0
                while j < wordLen:
                    # Adjust the head connections to take into account the compounding of two elements
                    if customWords[j].head > i:
                        customWords[j].head = customWords[j].head - 1
                    # Adjust the id's to take into account the removal of the compound word
                    if j > i:
                        customWords[j].id -=  1
                    j += 1

                # Remove the extra word
                wordLen -= 1
                del customWords[i]

        i += 1


    #depData = {"words":[],
    #       "arcs":[]}

    #for word in words:
    #    depData["words"].append({"text":word.text, "tag": word.pos})
    #    if word.head != 0:
    #        print(word, max(word.id-1, word.head-1))
    #        depData["arcs"].append({"start": min(word.id-1, word.head-1), "end": max(word.id-1, word.head-1), "label": word.deprel, "dir": "left" if word.head > word.id else "right"})
    
    # Spin up a webserver on port 5000 with the dependency tree using displacy
    #print(depData)
    #displacy.serve(depData, style="dep", manual=True)
        
    return customWords

def matchingFunction(words, startId=0):

    #words = compoundWords(words)

    wordsBak = words

    wordLen = len(words)

    tokenObject = []
    words2 = []

    i = 0
    while i < wordLen:
        #print(words[words[i].head-1], words[i].deprel, words[i].text)

        # If the word is recognized as a condition or constraint
        if words[i].deprel == "advcl":
            # Find the substructure for the condition or constraint
            # print("Advcl")
            
            condition = ""

            firstVal = 0
            firstValFilled = False

            k = 0

            # Go through the statement from the first word to the advcl deprel
            while k < i:
                x = k
                headRel = ""
                while headRel != "root":
                    # Set x to the head of x
                    x = wordsBak[x].head-1
                    #print(wordsBak[x].deprel, wordsBak[x].text)
                    if wordsBak[x].deprel == "advcl":
                        if not firstValFilled:
                            firstVal = k
                            firstValFilled = True
                        condition += " " + wordsBak[k].text
                        headRel = "root"
                    headRel = wordsBak[x].deprel
                k += 1
            
            condition += " " + wordsBak[i].text

            # print(condition)

            lastIndex = 0

            k = i+1
            while k < len(wordsBak):
                x = k
                headRel = ""
                while headRel != "root":
                    x = wordsBak[x].head-1
                    if wordsBak[x].deprel == "advcl":
                        condition += " " + wordsBak[k].text
                        lastIndex = k+1
                        headRel = "root"
                    headRel = wordsBak[x].deprel
                k += 1

            # print("Cac{" + condition + "}", lastIndex, firstVal)

            cacLen = lastIndex

            # Return the combination of the activation condition and the rest of the sentence
            if lastIndex < len(wordsBak) and wordsBak[lastIndex].deprel == "punct":
                statementRest = []
                # Skip over the following punctuation
                lastIndex += 1
                while lastIndex < len(wordsBak):
                    #statementRest += " " + wordsBak[lastIndex].text
                    statementRest.append(wordsBak[lastIndex])
                    lastIndex += 1

                # print("statementRest: ", statementRest)
                # print("Lengths:",  cacLen-firstVal, lastIndex, lastIndex-(cacLen-firstVal), len(wordsBak) )
                if firstVal == 0:
                    tokenObject = []

                    contents = []

                    words2.append(Word(
                        "","","",0,0,"","",0,0,0,"Cac",True,1
                        ))
                    words2 += matchingFunction(compoundWords(nlpPipeline(WordsToSentence(words[:cacLen]))))
                    #words2[0].setSymbol("Cac",1,True)
                    #words2[cacLen-1].setSymbol("Cac",2,True)
                    words2.append(Word("","","",0,0,"","",0,0,0,"Cac",True,2))
                    words2.append(words[cacLen])

                    contents += matchingFunction(compoundWords(nlpPipeline(condition)))
                    tokenObject.append(TokenEntry("Cac{"+contents[0].text, "",contents[0].id))
                    tokenObject += contents[1:]
                    #words[i].setSymbol("Cac",2,True)
                    tokenObject.append(TokenEntry("}"+wordsBak[cacLen].text, "punct",wordsBak[cacLen]))
                    contents = matchingFunction(compoundWords(nlpPipeline(WordsToSentence(words[cacLen+1:]))),lastIndex+2)

                    # Copy over the old placement information to the newly generated words for proper formatting
                    k = cacLen +1
                    while k < len(words):
                        index = k-cacLen-1
                        contents[index].id = words[k].id
                        contents[index].start = words[k].start
                        contents[index].end = words[k].end
                        contents[index].spaces = words[k].spaces

                        k += 1

                    # print("Contents are: '", contents[0].text, "'")
                    #tokenObject += contents
                    words2 += contents

                    #return tokenObject
                    return words2

        # If the word is an object
        if words[i].deprel == "obj":
            #print(words[i+1].text)
            # Can potentially check for the dep_ "cc" instead
            if i+1 < len(words) and (words[i+1].text.lower() == "or" or words[i+1].text.lower() == "and"):
                # print(words[i+1].text)
                j = i+2
                conjugated = False

                tokenObject.append(TokenEntry("Bdir("+words[i].text, "", i))
                words[i].setSymbol("Bdir", 1)
                tokenObject.append(TokenEntry("[" + words[i+1].text.upper() + "]", "", i+1))
                words[i+1].text = "[" + words[i+1].text.upper() + "]"

                # print("\n\n",tokenToText(tokenObject),"\n\n")

                while j < len(words):
                    #output += " " + words[j].text

                    # If the word has a conj dependency to the dobj, then add the text and set conjugated to true
                    if words[j].deprel == "conj" and words[words[j].head-1] == words[i]:
                        # print("This loop is active", words[j].deprel, words[words[j].head-1].text)
                        depIndex = j
                        conjugated = True
                        connected = True

                        k = i+2

                        # If connected add the preceeding words to the tokenObject
                        while k < j:
                            tokenObject.append(TokenEntry(words[k].text, "", k))
                            k += 1

                        # Add the current word to the tokenObject
                        tokenObject.append(TokenEntry(words[j].text, "", j))

                        # While the next word(s) are connected to the conj of the dobj, add them
                        while connected:
                           if j+1 < len(words) and words[words[j+1].head-1] ==  words[depIndex]:
                                tokenObject.append(TokenEntry(words[j+1].text, "", j+1))
                                #output += " " + words[j+1].text
                                j+=1
                           else:
                               words[j].setSymbol("Bdir", 2)
                               tokenObject.append(TokenEntry(")", ""))
                               connected = False
                               i=j
                        break
                    else:
                        j += 1
                        
                #if conjugated:
                    #print("This is conjugated")
                if not conjugated:
                    # print("This is not conjugated")
                    tokenObject.append(TokenEntry(words[i+2].text, "", i+2))
                    words[i+2].setSymbol("Bdir", 2)
                    tokenObject.append(TokenEntry(")", ""))
                    #print("i is: ", i, conjugated)
                    i += 2     
            else:
                #print("Else condition")
                tokenObject.append(TokenEntry(words[i].text, "Bdir", i))
                words[i].setSymbol("Bdir")
        
        #  Else if the word has an amod dependency type, check if the head is a symbol
        # that supports properties, if so, the word is a property of that symbol
        elif words[i].deprel == "amod":
            if words[words[i].head-1].deprel == "obj":
                #print(words[i].text, " Property of Bdir: ",  words[words[i].head-1].text)
                tokenObject.append(TokenEntry(words[i].text, "Bdir,p",i))
                words[i].setSymbol("Bdir,p")
            elif words[words[i].head-1].deprel == "iobj":
                #print(words[i].text, " Property of Bind: ",  words[words[i].head-1].text)
                tokenObject.append(TokenEntry(words[i].text, "Bind,p",i))
                words[i].setSymbol("Bind,p")
            elif words[words[i].head-1].deprel == "nsubj" and words[words[words[i].head-1].head-1].deprel == "root":
                #print(words[i].text, " Property of A: ",  words[words[i].head-1].text)
                tokenObject.append(TokenEntry(words[i].text, "A,p",i))
                words[i].setSymbol("A,p")
            else:
                tokenObject.append(TokenEntry(words[i].text, "",i))
             
        # Else if the word is the sentence root, handle it as an "Aim" (I) component
        elif words[i].deprel == "root":
            
            # If the word is connected to another word by a logical operator (and / or)
            if i+1 < len(words) and (words[i+1].text.lower() == "or" or words[i+1].text.lower() == "and"):
                # Handle the logical operator
                j = i+2
                conjugated = False

                tokenObject.append(TokenEntry("I("+words[i].text, "", i))
                words[i].setSymbol("I",1)
                tokenObject.append(TokenEntry("[" + words[i+1].text.upper() + "]", "", i+1))
                words[i+1].text = "[" + words[i+1].text.upper() + "]"

                # Positive lookahead, look for conj connection to the aim, add them if present
                while j < len(words):
                    # If the word has a conj dependency to the aim, then add the text and set conjugated to true
                    if words[j].deprel == "conj" and words[words[j].head-1] == words[i]:
                        #print("This loop is active", words[j].deprel, words[words[j].head-1].text)
                        depIndex = j
                        conjugated = True
                        connected = True

                        k = i+2

                        # If connected add the preceeding words to the tokenObject
                        while k < j:
                            tokenObject.append(TokenEntry(words[k].text, "", k))
                            k += 1

                        # Add the current word to the tokenObject
                        tokenObject.append(TokenEntry(words[j].text, "", j))

                        # While the next word(s) are connected to the conj of the aim, add them
                        while connected:
                           if j+1 < len(words) and words[words[j+1].head-1] == words[depIndex]:
                                tokenObject.append(TokenEntry(words[j+1].text, "", j+1))
                                output += " " + words[j+1].text
                                j+=1
                           else:
                               words[j].setSymbol("I", 2)
                               tokenObject.append(TokenEntry(")", ""))
                               connected = False
                               i=j
                        break
                    else:
                        j += 1
                        
                #if conjugated:
                #    print("Is conjugated")
                if not conjugated:
                #   print("Is not conjugated")
                    # Go through the rest of the sentence and check for conj connections, if none exist just add the next word
                    tokenObject.append(TokenEntry(words[i+2].text, "", i+2))
                    words[i+2].setSymbol("I", 2)
                    tokenObject.append(TokenEntry(")", ""))
                    i += 2

            # If no logical operator is present just add the symbol       
            else:
                tokenObject.append(TokenEntry(words[i].text, "I", i))
                words[i].setSymbol("I")
        
        # If the head of the word is the root, check the symbol dictionary for symbol matches
        elif words[words[i].head-1].deprel == "root":
            if words[i].deprel in SymbolDict:
                tokenObject.append(TokenEntry(words[i].text, SymbolDict[words[i].deprel], i))
                words[i].setSymbol(SymbolDict[words[i].deprel])
            else:
                tokenObject.append(TokenEntry(words[i].text, "", i))
        
        # If the relation is a ccomp then handle it as a direct object
        elif words[i].deprel == "amod" and words[words[i].head-1].deprel == "nsubj" and words[words[words[i].head-1].head-1].deprel == "ccomp":
            #print("\n\nAMOD NSUBJ OBJ\n\n")
            tokenObject.append(TokenEntry("("+words[i].text, "", i))
            words[i].setSymbol(words[i],"bdir", 1)
            tokenObject.append(TokenEntry(words[i+1].text, "",i+1))
            words[i+1].setSymbol(words[i+1],"bdir", 2)
            tokenObject.append(TokenEntry(")", ""))
            i += 1
        elif words[i].deprel == "nsubj" and words[words[i].head-1].deprel == "ccomp":
            #print("\n\nNSUBJ CCOMP OBJ\n\n")
            tokenObject.append(TokenEntry(words[i].text, "",i))
        
        # If the word had no matches, simply add it to the parsed sentence
        else:
            if words[i].deprel == "punct":
                #print("Adding punct: '", words[i].text, "'")
                tokenObject.append(TokenEntry(words[i].text, "punct",i))
            else:
                #print("Adding word: '", words[i].text, "' deprel: ", words[i].deprel)
                tokenObject.append(TokenEntry(words[i].text, "",i))
        i += 1

    print("\n\nTokens:\n")
    print(tokenToText(tokenObject))
    print(WordsToSentence2)

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

def WordsToSentence2(words):
    i = 0

    sentence = ""

    while i < len(words):
        sentence += words[i].buildString()
        i += 1
    
    return sentence