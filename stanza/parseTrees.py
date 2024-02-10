import json
import stanza
from spacy import displacy

from utility import compoundWordsMiddleware

filename = "../data/input.json"

global nlp
nlp = stanza.Pipeline('en', use_gpu=True,
    processors='tokenize,pos,lemma,depparse,ner', 
    download_method=stanza.DownloadMethod.REUSE_RESOURCES,
    logging_level="fatal")

with open(filename, "r") as input:
    
    jsonData = json.load(input)

    i = 0

    print("Running with ", len(jsonData), " items.")
    textDocs = []
    while i < len(jsonData): 
        textDocs.append(jsonData[i]['baseTx'])
        i+=1

    docs = nlp.bulk_process(textDocs)

    i = 0
    while i < len(docs):
        base = jsonData[i]['baseTx']
        
        doc = docs[i]

        depData = {"words":[],
           "arcs":[]}

    # Based on the example found at: 
    # https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
        for sentence in doc.sentences:
            sentence.words = compoundWordsMiddleware(sentence.words)
            for word in sentence.words:
                # Generating the data structure for displacy visualization
                depData["words"].append({"text":word.text, "tag": word.pos})
                if word.head != 0:
                    depData["arcs"].append({
                        "start": min(word.id-1, word.head-1), 
                        "end": max(word.id-1, word.head-1), 
                        "label": word.deprel, "dir": "left" if word.head > word.id else "right"})

        html = displacy.render(depData, style="dep",
                        manual=True, page=True, minify=True)
        
        with open("../data/" + str(i)+"-"+jsonData[i]["name"]+".html", "w") as outputFile:
            outputFile.write(html)
            outputFile.close

        i += 1