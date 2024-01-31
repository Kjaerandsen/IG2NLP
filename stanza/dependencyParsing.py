import stanza
import pandas as pd
import sys
from spacy import displacy

from matcherAsFunctionAdvanced import compoundWords

nlp = stanza.Pipeline('en', use_gpu=False)
# Take the system arguments
args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\n'+
          'dependencyParsing "Input string here"')
    sys.exit()

# Take the input string
doc = nlp(args[1])

print('Now printing named entities\n')

for sentence in doc.sentences:
    print("Entity:")
    print(sentence.ents)

depData = {"words":[],
           "arcs":[]}

# Create a table with the relevant information from the doc
# Based on the example found at: 
# https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
print('Now printing dependencies\n')
df = pd.DataFrame(columns=["Word", "POS", "Head id", "Head word", "Dependency"])
for sentence in doc.sentences:
    sentence.words = compoundWords(sentence.words)
    for word in sentence.words:
        df = df._append({
            "Word": word.text, "POS":word.pos, "Head id":word.head, 
            "Head word":sentence.words[word.head-1].text if word.head > 0 else "root", 
            "Dependency": word.deprel}, ignore_index=True)
        
        # Generating the data structure for displacy visualization
        depData["words"].append({"text":word.text, "tag": word.pos})
        if word.head != 0:
            depData["arcs"].append({
                "start": min(word.id-1, word.head-1), 
                "end": max(word.id-1, word.head-1), 
                "label": word.deprel, "dir": "left" if word.head > word.id else "right"})

print(df)

print('Now printing constituency tree\n')

for sentence in doc.sentences:
    print(sentence.constituency)

# Spin up a webserver on port 5000 with the dependency tree using displacy
displacy.serve(depData, style="dep", manual=True)