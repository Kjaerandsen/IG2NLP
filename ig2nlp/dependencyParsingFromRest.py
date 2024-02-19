import pandas as pd
import sys
from spacy import displacy
import requests

from utility import Word, compoundWordsMiddlewareWords, loadEnvironmentVariables

# Take the system arguments
args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\n'+
          'dependencyParsing "Input string here"')
    sys.exit()

# Take the input string 
out = [{"baseTx":args[1]}]

#print(out, json.dumps(out))
env = loadEnvironmentVariables()
response = requests.post(env['flaskURL'], json = out)
displacyPort = env['displacyPort']

# Delete the environment variables dictionary
del env

jsonRes = response.json()

words=[]
for word in jsonRes[0]:
    words.append(
        Word(
            word['text'],
            word['pos'],
            word['deprel'],
            word['head'],
            word['id'],
            word['lemma'],
            word['xpos'],
            word['feats'],
            word['start'],
            word['end'],
            word['spaces'],
            word['symbol'],
            word['nested'],
            word['position'],
            word['ner'],
            word['logical'],
            word['corefid'],
            word['coref'],
            word['corefScope'],
            word['isRepresentative']
        )
    )

print('Now printing named entities\n')

depData = {"words":[],
           "arcs":[]}

# Create a table with the relevant information from the doc
# Based on the example found at: 
# https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
print('Now printing dependencies\n')

pd.set_option('display.max_rows', None)

#for sentence in doc.sentences:
df = pd.DataFrame(columns=["Word", "POS", "Head id", "Head word", "Dependency", "Lemma", "Feats"])
words = compoundWordsMiddlewareWords(words)
for word in words:
    df = df._append({
        "Word": word.text, "POS":word.pos, "Head id":word.head, 
        "Head word":words[word.head-1].text if word.head > 0 else "root", 
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
       
# Spin up a webserver on port 5000 with the dependency tree using displacy
displacy.serve(depData, style="dep", manual=True, port=displacyPort)