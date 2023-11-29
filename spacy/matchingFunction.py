import spacy
import pandas as pd
import sys


args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\ndependencyParsing "Input string here"')
    sys.exit()

nlp = spacy.load("en_core_web_sm")

# Take the input string
doc = nlp(args[1])

# Create and print a table of releveant values of the words
df = pd.DataFrame(columns=["Token", "Lemma", "POS", "Tag", "Dependency", "Entity"])
for token in doc:
    df = df._append({"Token": token.text, "Lemma":token.lemma_, "POS": token.pos_, "Tag": token.tag_, "Dependency": token.dep_, 
                    "Entity": token.ent_type_}, ignore_index=True)
    
print(df)

parsedDoc = []

# Dictionary of symbols for parsing
symbolDict = {"pobj":"Bind","dobj":"Bdir","aux":"D","nsubj":"A","ROOT":"I"}

for token in doc:
    #print(token.head.dep_, token.dep_, token.text)

    if token.text == "%" or token.text.lower == "percent":
        parsedDoc[-1] = {"text":parsedDoc[-1]['text'] + token.text, "type":symbolDict[token.dep_]}
    else:
        if token.dep_ == "pobj":
            parsedDoc.append({"text":token.text, "type":"Bind"})
        elif token.dep_ == "dobj":
            parsedDoc.append({"text":token.text, "type":"Bdir"})
        elif token.head.dep_ == "ROOT":
            if token.dep_ in symbolDict:
                parsedDoc.append({"text":token.text, "type":symbolDict[token.dep_]})
            else:
                parsedDoc.append({"text":token.text, "type":""})
        else:
            parsedDoc.append({"text":token.text, "type":""})

#print(parsedDoc)

#for doc in parsedDoc:
#    print(doc)

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
print(outputText)
    
# Print results to a file
print("input: "+args[1]+"\noutput:"+outputText+"\n", file=open('output.txt', 'a'))
