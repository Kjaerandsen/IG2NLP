import stanza
import pandas as pd
import sys
from spacy import displacy

from utility import env, compoundWordsHandler, convertWordFormat
from nlp import initializePipeline

# Take the system arguments
args = sys.argv

# Check if an input was given
if len(args)<2:
   print('Error: a string must be passed with the function in the format:\n'+
        'dependencyParsing "Input string here"')
   sys.exit()

nlp = initializePipeline(
      env['useGPU'], env['coref'], env['downloadMethod'], env['logLevel'], env['pipeline'])

displacyPort = env['displacyPort']

# Delete the environment variables dictionary
del env

# Take the input string
doc:stanza.Document = nlp(args[1])

print('Now printing named entities\n')

print(doc.ents)

print("DOC DATA\n", doc.__dict__.keys())

print("Coref chains:\n")

for item in doc.coref:
   print("Index: ", item.index, "| Mentions: ",[value.__dict__ for value in item.mentions], 
        "| Representative text: ", item.representative_text, 
        "| Representative id: ", item.representative_index)

depData = {"words":[],
         "arcs":[]}

# Create a table with the relevant information from the doc
# Based on the example found at: 
# https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
print('Now printing dependencies\n')

pd.set_option('display.max_rows', None)

lastWord = 0
for sentence in doc.sentences:
   sentenceWords = convertWordFormat(sentence.words)
   df = pd.DataFrame(columns=["Word", "POS", "Head id", "Head word", "Dependency", "Lemma", "Feats"])
   sentenceWords = compoundWordsHandler(sentenceWords)
   for word in sentenceWords:
      df = df._append({
         "Word": word.text, "POS":word.pos, "Head id":word.head, 
         "Head word":sentenceWords[word.head-1].text if word.head > 0 else "root", 
         "Dependency": word.deprel, "Lemma": word.lemma, "Feats":word.feats}, ignore_index=True)
   
   # Generating the data structure for displacy visualization
      depData["words"].append({"text":word.text, "tag": word.pos})
      if word.head not in [0,-1]:
         depData["arcs"].append({
            "start": min(word.id-1 + lastWord, word.head + lastWord), 
            "end": max(word.id-1 + lastWord, word.head + lastWord), 
            "label": word.deprel, "dir": "left" if word.head > word.id-1 else "right"})
   lastWord += len(sentenceWords)      
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
displacy.serve(depData, style="dep", manual=True, port=displacyPort)