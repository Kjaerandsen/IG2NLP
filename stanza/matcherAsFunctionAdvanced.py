import stanza
import pandas as pd

def Matcher(text):
    nlp = stanza.Pipeline('en', use_gpu=False)

    # Take the input string
    doc = nlp(text)

    #depData = {"words":[],
    #       "arcs":[]}

    # Create a table with the relevant information from the doc
    # Based on the example found at: https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
    #print('Now printing dependencies\n')
    #df = pd.DataFrame(columns=["Word", "POS", "Head id", "Head word", "Dependency"])
    #for sentence in doc.sentences:
    #    for word in sentence.words:
    #        df = df._append({"Word": word.text, "POS":word.pos, "Head id":word.head, "Head word":sentence.words[word.head-1].text if word.head > 0 else "root", "Dependency": word.deprel}, ignore_index=True)
    #        
    #        # Generating the data structure for displacy visualization
    #        depData["words"].append({"text":word.text, "tag": word.pos})
    #        if word.head != 0:
    #            depData["arcs"].append({"start": min(word.id-1, word.head-1), "end": max(word.id-1, word.head-1), "label": word.deprel, "dir": "left" if word.head > word.id else "right"})

    #print(df)

    parsedDoc = []

    # Dictionary of symbols for parsing
    symbolDict = {"pobj":"Bind","obj":"Bdir","aux":"D","nsubj":"A"}
    
    words = doc.sentences[0].words
    wordsBak = doc.sentences[0].words

    i = 0
    while i < len(words):
        #token = doc[i]
        #print(words[words[i].head-1], words[i].deprel, words[i].text)
        if words[i].deprel == "advcl":
            # Find the substructure for the condition or constraint
            print("Advcl")
            
            condition = ""

            firstVal = 0
            firstValFilled = False

            k = 0
            while k < i:
                x = k
                headRel = ""
                while headRel != "root":
                    x = wordsBak[x].head-1
                    print(wordsBak[x].deprel)
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
                while lastIndex < len(wordsBak):
                    statementRest += " " + wordsBak[lastIndex].text
                    lastIndex += 1

                print("statementRest: ", statementRest)
                print("Lengths:",  cacLen-firstVal, lastIndex, lastIndex-(cacLen-firstVal), len(wordsBak) )
                if firstVal == 0:
                    return "Cac{"+ Matcher(condition) + "} " + Matcher(statementRest)     
        if words[i].deprel == "compound" and words[i].text != "": 
            words[i+1].text = words[i].text + " " + words[i+1].text
            words[i].text = ""
        elif words[i].deprel == "obj":
            #print(words[i+1].text)
            # Can potentially check for the dep_ "cc" instead
            if i+1 < len(words) and (words[i+1].text.lower() == "or" or words[i+1].text.lower() == "and"):
                print(words[i+1].text)
                j = i+2
                conjugated = False
                output = words[i].text + " [" + words[i+1].text.upper() + "]"
                while j < len(words):
                    output += " " + words[j].text
                    if words[j].deprel == "conj" and words[words[j].head-1] == words[i]:
                        print("This loop is active", words[j].deprel, words[words[j].head-1].text)
                        depIndex = j
                        conjugated = True
                        connected = True
                        while connected:
                           if j+1 < len(words) and words[words[j+1].head-1] ==  words[depIndex]:
                                output += " " + words[j+1].text
                                j+=1
                           else:
                               connected = False
                               i=j
                        break
                    else:
                        j += 1
                        
                if conjugated:
                    parsedDoc.append({"text":output,"type":"Bdir"})
                else:
                    print("i is: ", i, conjugated)
                    # Go through the rest of the sentence and check for conj connections, if none exist just add the next word
                    parsedDoc.append({"text":words[i].text + " [" + words[i+1].text.upper() + "] " + words[i+2].text, "type":"Bdir"})
                    i += 2     
            else:
                parsedDoc.append({"text":words[i].text, "type":"Bdir"})
        elif words[i].deprel == "root":
            if i+1 < len(words) and (words[i+1].text.lower() == "or" or words[i+1].text.lower() == "and"):
                j = i+2
                conjugated = False
                output = words[i].text + " [" + words[i+1].text.upper() + "]"
                while j < len(words):
                    output += " " + words[j].text
                    if words[j].deprel == "conj" and words[words[j].head-1] == words[i]:
                        print("This loop is active", words[j].deprel, words[words[j].head-1].text)
                        depIndex = j
                        conjugated = True
                        connected = True
                        while connected:
                           if j+1 < len(words) and words[words[j+1].head-1] ==  words[depIndex]:
                                output += " " + words[j+1].text
                                j+=1
                           else:
                               connected = False
                               i=j
                        break
                    else:
                        j += 1
                        
                if conjugated:
                    parsedDoc.append({"text":output,"type":"I"})
                else:
                    print("i is: ", i, conjugated)
                    # Go through the rest of the sentence and check for conj connections, if none exist just add the next word
                    parsedDoc.append({"text":words[i].text + " [" + words[i+1].text.upper() + "] " + words[i+2].text, "type":"I"})
                    i += 2
                        
            else:
                parsedDoc.append({"text":words[i].text, "type":"I"})
        elif words[words[i].head-1].deprel == "root":
            if words[i].deprel in symbolDict:
                parsedDoc.append({"text":words[i].text, "type":symbolDict[words[i].deprel]})
            else:
                parsedDoc.append({"text":words[i].text, "type":""})
        elif words[i].deprel == "amod" and words[words[i].head-1].deprel == "nsubj" and words[words[words[i].head-1].head-1].deprel == "ccomp":
            parsedDoc.append({"text":words[i].text + " " + words[words[i].head-1].text, "type": "Bdir"})
            i += 1
        elif words[i].deprel == "nsubj" and words[words[i].head-1].deprel == "ccomp":
            parsedDoc.append({"text":words[i].text, "type": "Bdir"})
        else:
            parsedDoc.append({"text":words[i].text, "type":""})
        i += 1

    outputText = ""

    for i in range(len(parsedDoc)):
        if parsedDoc[i]['type'] == "":
            if parsedDoc[i]['text'] == ".":
                stringAsList = list(outputText)
                stringAsList[-1] = "."
                outputText = ''.join(stringAsList)
            else:
                outputText = outputText + parsedDoc[i]['text'] + " "
        else:
            outputText = outputText+parsedDoc[i]['type'] + "(" + parsedDoc[i]['text'] + ") "
    #print(outputText)

    return outputText


