import json
import stanza
from spacy import displacy

from utility.utility import compoundWordsHandler, convertWordFormat, env

filename = "../data/inputRegFull.json"

nlp = stanza.Pipeline('en', use_gpu=env['useGPU'],
   processors='tokenize,pos,lemma,depparse,ner,mwt', 
   package={
      "tokenize": "combined",
      "mwt": "combined",
      "pos": "combined_electra-large",
      "depparse": "combined_electra-large",
      "lemma": "combined_charlm",
      "ner": "ontonotes-ww-multi_charlm"
   },
   download_method=env['downloadMethod'],
   logging_level=env['logLevel']
   )

# Delete the environment variables dictionary
del env

with open(filename, "r") as input:
   
   jsonData = json.load(input)

   i = 0

   print("Running with ", len(jsonData), " items.")
   textDocs = []
   while i < len(jsonData): 
      textDocs.append(jsonData[i]['baseTx'])
      i+=1

   docs = []
   batchSize = 30
   while len(textDocs) > batchSize:
      pipelineResults = nlp.bulk_process(textDocs[:batchSize])
      for doc in pipelineResults: docs.append(doc)
      textDocs = textDocs[batchSize:]
   # Add the remaining items
   pipelineResults = nlp.bulk_process(textDocs)
   for doc in pipelineResults: docs.append(doc)
   #docs = nlp.bulk_process(textDocs)

   i = 0
   while i < len(docs):
      base = jsonData[i]['baseTx']
      
      doc = docs[i]

      depData = {"words":[],
         "arcs":[]}

   # Based on the example found at: 
   # https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
      for sentence in doc.sentences:
         sentence.words = compoundWordsHandler(convertWordFormat(sentence.words))
         for word in sentence.words:
            # Generating the data structure for displacy visualization
            depData["words"].append({"text":word.text, "tag": word.pos})
            if word.head != -1:
               depData["arcs"].append({
                  "start": min(word.id-1, word.head), 
                  "end": max(word.id-1, word.head), 
                  "label": word.deprel, "dir": "left" if word.head > word.id-1 else "right"})

      html = displacy.render(depData, style="dep",
                  manual=True, page=True, minify=True)
      
      with open("../data/" + str(i)+"-"+jsonData[i]["name"]+".html", "w") as outputFile:
         outputFile.write(html)
         outputFile.close

      i += 1
