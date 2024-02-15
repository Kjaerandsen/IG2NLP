import stanza
import pandas as pd
import sys
from spacy import displacy

from utility import compoundWordsMiddleware

# Take the system arguments
args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\n'+
          'dependencyParsing "Input string here"')
    sys.exit()

nlp = stanza.Pipeline('en', use_gpu=True, 
    processors='tokenize,pos,lemma,constituency,depparse,ner,mwt,coref', 
    package={
        "tokenize": "combined",
        "mwt": "combined",
        "ner": ["ontonotes_charlm","conll03_charlm"],
        "pos": "combined_electra-large",
        "depparse": "combined_electra-large",
        "lemma": "combined_charlm",
        "ner": "ontonotes-ww-multi_charlm"
    },
    download_method=stanza.DownloadMethod.REUSE_RESOURCES,
    logging_level="fatal")

# Take the input string
doc = nlp(args[1])

print('Now printing named entities\n')

#for sentence in doc.sentences:
#    print("Entity:")
#    print(sentence.ents)

print(doc.ents)

print("DOC DATA\n", doc.__dict__.keys())

print("Coref chains:\n")

#print("DOC coref: ", doc.coref)

for item in doc.coref:
    print("Index: ", item.index, "| Mentions: ",[value.__dict__ for value in item.mentions], 
          "| Representative text: ", item.representative_text, 
          "| Representative id: ", item.representative_index)
    #print(item.__dict__)
    #print(item.__dict__.keys())

print(doc.sentences[0].tokens[0:2])
print(doc.sentences[0].tokens[8:10])

depData = {"words":[],
           "arcs":[]}

# Create a table with the relevant information from the doc
# Based on the example found at: 
# https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
print('Now printing dependencies\n')

pd.set_option('display.max_rows', None)

for sentence in doc.sentences:
    df = pd.DataFrame(columns=["Word", "POS", "Head id", "Head word", "Dependency", "Lemma", "Feats"])
    sentence.words = compoundWordsMiddleware(sentence.words)
    for word in sentence.words:
        df = df._append({
            "Word": word.text, "POS":word.pos, "Head id":word.head, 
            "Head word":sentence.words[word.head-1].text if word.head > 0 else "root", 
            "Dependency": word.deprel, "Lemma": word.lemma, "Feats":word.feats}, ignore_index=True)
    
    # Generating the data structure for displacy visualization
        depData["words"].append({"text":word.text, "tag": word.pos})
        if word.head != 0:
            depData["arcs"].append({
                "start": min(word.id-1, word.head-1), 
                "end": max(word.id-1, word.head-1), 
                "label": word.deprel, "dir": "left" if word.head > word.id else "right"})
    print("\nWords: ")   
    print(df)
    df = pd.DataFrame(columns=["Token", "POS", "Head id", "Dependency", "NER"])
    for token in sentence.tokens:
        df = df._append({
            "Token": token.text, "POS":token.words[0].pos, "Head id":token.words[0].head,  
            "Dependency": token.words[0].deprel, "NER": token.ner}, ignore_index=True)
    print("\nTokens with NER: ")
    print(df)
    
        
       


print('Now printing constituency tree\n')

for sentence in doc.sentences:
    print(sentence.constituency)

# Spin up a webserver on port 5000 with the dependency tree using displacy
displacy.serve(depData, style="dep", manual=True, port=5001)