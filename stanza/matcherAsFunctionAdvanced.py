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
        print(self.text, self.type)
        if self.id == None:
            return self.text
        elif self.type == "":
            return " " + self.text
        elif self.type == "punct":
            if self.text[0] == " " and len(self.text >= 1):
                self.text = self.text[1:]
                print("Text is: ", self.text)
            return self.text
        else:
            return " " + self.type + "(" + self.text + ")"

def Matcher(text):
    #words = nlpPipeline(text)

    #return matchingFunction(words)
    return tokenToText(matchingFunction(nlpPipeline(text)))

# Takes a sentence as a string, returns the nlp pipeline results for the string
def nlpPipeline(text):
    nlp = stanza.Pipeline('en', use_gpu=False, download_method=None)

    # Take the input string
    doc = nlp(text)

    return doc.sentences[0].words

# Takes the words from the nlp pipeline and combines combine words to a single word
def compoundWords(words):
    
    i = 0
    wordLen = len(words)

    #print("type is: ", type(words[0]), " " , wordLen)
    while i < wordLen:
        #print(words[i])

        # If the word is a compound word
        if words[i].deprel == "compound" and words[i].text != "" and words[i].head-1 == i+1: 
            #words[i+1].start_char = words[i].start_char
            # Set the text to the compound word and the following word
            words[i+1].text = words[i].text + " " + words[i+1].text
            
            # Go through the words and adjust the connections between the words to account
            # for the combination of compound words into single words
            j = 0
            while j < wordLen:
                # Adjust the head connections to take into account the compounding of two elements
                if words[j].head > i+1:
                    words[j].head = words[j].head - 1
                # Adjust the id's to take into account the removal of the compound word
                if j >= i:
                    words[j].id -=  1
                j += 1
            # Remove the old compound
            wordLen -= 1
            del words[i]
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
        
    return words

def matchingFunction(words, startId=0):

    words = compoundWords(words)

    #parsedDoc = []
    wordsBak = words

    wordLen = len(words)

    tokenObject = []

    #tokenObject.append(TokenEntry())

    i = 0
    while i < wordLen:
        #token = doc[i]
        #print(words[words[i].head-1], words[i].deprel, words[i].text)

        # If the word is recognized as a condition or constraint
        if words[i].deprel == "advcl":
            # Find the substructure for the condition or constraint
            print("Advcl")
            
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
                    print(wordsBak[x].deprel, wordsBak[x].text)
                    if wordsBak[x].deprel == "advcl":
                        if not firstValFilled:
                            firstVal = k
                            firstValFilled = True
                        condition += " " + wordsBak[k].text
                        headRel = "root"
                    headRel = wordsBak[x].deprel
                k += 1
            
            condition += " " + wordsBak[i].text

            print(condition)

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

            print("Cac{" + condition + "}", lastIndex, firstVal)

            cacLen = lastIndex

            if lastIndex < len(wordsBak) and wordsBak[lastIndex].deprel == "punct":
                statementRest = ""
                # Skip over the following punctuation
                lastIndex += 1
                while lastIndex < len(wordsBak):
                    statementRest += " " + wordsBak[lastIndex].text
                    lastIndex += 1

                print("statementRest: ", statementRest)
                print("Lengths:",  cacLen-firstVal, lastIndex, lastIndex-(cacLen-firstVal), len(wordsBak) )
                if firstVal == 0:
                    tokenObject = []

                    
                    contents = []
                    contentLen = len
                    contents += matchingFunction(nlpPipeline(condition))
                    tokenObject.append(TokenEntry("Cac{"+contents[0].text, "",contents[0].id))
                    tokenObject += contents[1:]
                    tokenObject.append(TokenEntry("}"+wordsBak[cacLen].text, "punct",wordsBak[cacLen]))
                    contents = matchingFunction(nlpPipeline(statementRest),lastIndex+2)
                    print("Contents are: '", contents[0].text, "'")
                    tokenObject += contents

                    return tokenObject
                    #return matchingFunction(nlpPipeline(condition)) + "} " + matchingFunction(nlpPipeline(statementRest),lastIndex+1)     

        # If the word is an object
        if words[i].deprel == "obj":
            #print(words[i+1].text)
            # Can potentially check for the dep_ "cc" instead
            if i+1 < len(words) and (words[i+1].text.lower() == "or" or words[i+1].text.lower() == "and"):
                print(words[i+1].text)
                j = i+2
                conjugated = False
                #output = words[i].text + " [" + words[i+1].text.upper() + "]"

                tokenObject.append(TokenEntry("Bdir("+words[i].text, "", i))
                tokenObject.append(TokenEntry("[" + words[i+1].text.upper() + "]", "", i+1))

                print("\n\n",tokenToText(tokenObject),"\n\n")

                while j < len(words):
                    #output += " " + words[j].text

                    # If the word has a conj dependency to the dobj, then add the text and set conjugated to true
                    if words[j].deprel == "conj" and words[words[j].head-1] == words[i]:
                        print("This loop is active", words[j].deprel, words[words[j].head-1].text)
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
                               tokenObject.append(TokenEntry(")", ""))
                               connected = False
                               i=j
                        break
                    else:
                        j += 1
                        
                if conjugated:
                    print("This is conjugated")
                    #parsedDoc.append({"text":output,"type":"Bdir"})
                else:
                    print("This is not conjugated")
                    tokenObject.append(TokenEntry(words[i+2].text, "", i+2))
                    tokenObject.append(TokenEntry(")", ""))
                    print("i is: ", i, conjugated)
                    #parsedDoc.append({"text":words[i].text + " [" + words[i+1].text.upper() + "] " + words[i+2].text, "type":"Bdir"})
                    i += 2     
            else:
                print("Else condition")
                tokenObject.append(TokenEntry(words[i].text, "Bdir", i))
                #parsedDoc.append({"text":words[i].text, "type":"Bdir"})
        
        #  Else if the word has an amod dependency type, check if the head is a symbol
        # that supports properties, if so, the word is a property of that symbol
        elif words[i].deprel == "amod":
            if words[words[i].head-1].deprel == "obj":
                print(words[i].text, " Property of Bdir: ",  words[words[i].head-1].text)
                tokenObject.append(TokenEntry(words[i].text, "Bdir,p",i))
            elif words[words[i].head-1].deprel == "iobj":
                print(words[i].text, " Property of Bind: ",  words[words[i].head-1].text)
                tokenObject.append(TokenEntry(words[i].text, "Bind,p",i))
            elif words[words[i].head-1].deprel == "nsubj" and words[words[words[i].head-1].head-1].deprel == "root":
                print(words[i].text, " Property of A: ",  words[words[i].head-1].text)
                tokenObject.append(TokenEntry(words[i].text, "A,p",i))
            else:
                tokenObject.append(TokenEntry(words[i].text, "",i))
             
        # Else if the word is the sentence root, handle it as an "Aim" (I) component
        elif words[i].deprel == "root":
            
            # If the word is connected to another word by a logical operator (and / or)
            if i+1 < len(words) and (words[i+1].text.lower() == "or" or words[i+1].text.lower() == "and"):
                # Handle the logical operator
                j = i+2
                conjugated = False
                #output = words[i].text + " [" + words[i+1].text.upper() + "]"

                tokenObject.append(TokenEntry("I("+words[i].text, "", i))
                tokenObject.append(TokenEntry("[" + words[i+1].text.upper() + "]", "", i+1))

                # Positive lookahead, look for conj connection to the aim, add them if present
                while j < len(words):
                    #output += " " + words[j].text

                    # If the word has a conj dependency to the aim, then add the text and set conjugated to true
                    if words[j].deprel == "conj" and words[words[j].head-1] == words[i]:
                        print("This loop is active", words[j].deprel, words[words[j].head-1].text)
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
                               tokenObject.append(TokenEntry(")", ""))
                               connected = False
                               i=j
                        break
                    else:
                        j += 1
                        
                if conjugated:
                    print("Is conjugated")
                    #parsedDoc.append({"text":output,"type":"I"})
                else:
                    print("Is not conjugated")
                    # Go through the rest of the sentence and check for conj connections, if none exist just add the next word
                    tokenObject.append(TokenEntry(words[i+2].text, "", i+2))
                    tokenObject.append(TokenEntry(")", ""))
                    #parsedDoc.append({"text":words[i].text + " [" + words[i+1].text.upper() + "] " + words[i+2].text, "type":"I"})
                    i += 2

            # If no logical operator is present just add the symbol       
            else:
                tokenObject.append(TokenEntry(words[i].text, "I", i))
                #parsedDoc.append({"text":words[i].text, "type":"I"})
        
        # If the head of the word is the root, check the symbol dictionary for symbol matches
        elif words[words[i].head-1].deprel == "root":
            if words[i].deprel in SymbolDict:
                tokenObject.append(TokenEntry(words[i].text, SymbolDict[words[i].deprel], i))
                #parsedDoc.append({"text":words[i].text, "type":SymbolDict[words[i].deprel]})
            else:
                tokenObject.append(TokenEntry(words[i].text, "", i))
                #parsedDoc.append({"text":words[i].text, "type":""})
        
        # If the relation is a ccomp then handle it as a direct object
        elif words[i].deprel == "amod" and words[words[i].head-1].deprel == "nsubj" and words[words[words[i].head-1].head-1].deprel == "ccomp":
            print("\n\nAMOD NSUBJ OBJ\n\n")
            tokenObject.append(TokenEntry("("+words[i].text, "", i))
            tokenObject.append(TokenEntry(words[i+1].text, "",i+1))
            tokenObject.append(TokenEntry(")", ""))
            #parsedDoc.append({"text":words[i].text + " " + words[words[i].head-1].text, "type": "Bdir"})
            i += 1
        elif words[i].deprel == "nsubj" and words[words[i].head-1].deprel == "ccomp":
            print("\n\nNSUBJ CCOMP OBJ\n\n")
            tokenObject.append(TokenEntry(words[i].text, "",i))
            #parsedDoc.append({"text":words[i].text, "type": "Bdir"})
        
        # If the word had no matches, simply add it to the parsed sentence
        else:
            if words[i].deprel == "punct":
                print("Adding punct: '", words[i].text, "'")
                tokenObject.append(TokenEntry(words[i].text, "punct",i))
                #parsedDoc.append({"text":words[i].text, "type":"punct"})
            else:
                print("Adding word: '", words[i].text, "' deprel: ", words[i].deprel)
                tokenObject.append(TokenEntry(words[i].text, "",i))
                #parsedDoc.append({"text":words[i].text, "type":""})
        i += 1

    #outputText = ""

    print("\n\nTokens:\n")
    print(tokenToText(tokenObject))

    #for i in range(len(parsedDoc)):
    #    if parsedDoc[i]['type'] == "":
            #if parsedDoc[i]['text'] == ".":
            #    stringAsList = list(outputText)
            #    stringAsList[-1] = "."
            #    outputText = ''.join(stringAsList)
            #else:
    #        outputText = outputText + " " + parsedDoc[i]['text']
    #    elif parsedDoc[i]['type'] == "punct":
    #        outputText = parsedDoc[i]['text']
    #    else:
    #        outputText = outputText+ " " + parsedDoc[i]['type'] + "(" + parsedDoc[i]['text'] + ")"

    #outputText = tokenToText(tokenObject)

    # Remove whitespace before the sentence start
    #while outputText[0] == " ":
    #    outputText = outputText[1:]
    #print("Returning output: ", outputText)
    
    #return outputText
    return tokenObject

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