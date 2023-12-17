import stanza
import pandas as pd
import sys


args = sys.argv

def Matcher(text):
    nlp = stanza.Pipeline('en', use_gpu=False)

    # Take the input string
    doc = nlp(text)

    depData = {"words":[],
           "arcs":[]}

    # Create a table with the relevant information from the doc
    # Based on the example found at: https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
    print('Now printing dependencies\n')
    df = pd.DataFrame(columns=["Word", "POS", "Head id", "Head word", "Dependency"])
    for sentence in doc.sentences:
        for word in sentence.words:
            df = df._append({"Word": word.text, "POS":word.pos, "Head id":word.head, "Head word":sentence.words[word.head-1].text if word.head > 0 else "root", "Dependency": word.deprel}, ignore_index=True)
            
            # Generating the data structure for displacy visualization
            depData["words"].append({"text":word.text, "tag": word.pos})
            if word.head != 0:
                depData["arcs"].append({"start": min(word.id-1, word.head-1), "end": max(word.id-1, word.head-1), "label": word.deprel, "dir": "left" if word.head > word.id else "right"})

    print(df)

    parsedDoc = []

    # Dictionary of symbols for parsing
    symbolDict = {"pobj":"Bind","obj":"Bdir","aux":"D","nsubj":"A","root":"I"}
    
    words = doc.sentences[0].words

    i = 0
    while i < len(words):
        print(words[i].text, words[i].deprel, words[words[i].head-1].text)
        #print(words[words[i].head].deprel, words[i].deprel, words[i].text)
        if words[i].text == "%" or words[i].text.lower == "percent":
            parsedDoc[-1] = {"text":parsedDoc[-1]['text'] + words[i].text, "type":symbolDict[words[i].deprel]}
        else:
            if words[i].deprel == "pobj":
                parsedDoc.append({"text":words[i].text, "type":"Bind"})
            elif words[i].deprel == "obj":
                parsedDoc.append({"text":words[i].text, "type":"Bdir"})
            elif words[i].deprel == "root":
                parsedDoc.append({"text":words[i].text, "type":"I"})
            elif words[words[i].head-1].deprel == "root":
                if words[i].deprel in symbolDict:
                    parsedDoc.append({"text":words[i].text, "type":symbolDict[words[i].deprel]})
                else:
                    parsedDoc.append({"text":words[i].text, "type":""})
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

    return outputText
