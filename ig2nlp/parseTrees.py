import json
import stanza
from spacy import displacy
import argparse

from utility import compoundWordsHandler, logicalOperatorHandler, convertWordFormat, env

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", 
   help="input file, defaults to json extension, i.e. input is treated as input.json")
parser.add_argument("-s", "--single", 
   help="single mode, run one at a time instead of batching the nlp pipeline.", 
   action="store_true")
parser.add_argument("-b", "--batch", 
   help="Batch size for the nlp pipeline. Lower values require less memory,"+
   " recommended values between 10 and 30, 0 batches everything. Default 30.")
args = parser.parse_args()

i = -1
if not args.input:
   filename = "../data/input.json"
else:
   filename = "../data/"+args.input+".json"

if args.batch:
   batchSize = int(args.batch)
else:
   batchSize = 30

if args.single:
   batchSize = 1

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

      # For multi-sentence docs a counter is kept of the last id of the previous sentence
      # to make the connections accurate for new sentences, as they all originate from 0.
      lastWord = 0
   # Based on the example found at: 
   # https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
      for sentence in doc.sentences:
         sentence.words = logicalOperatorHandler(
            compoundWordsHandler(convertWordFormat(sentence.words)))
         for word in sentence.words:
            # Generating the data structure for displacy visualization
            depData["words"].append({"text":word.text, "tag": word.pos})
            if word.head not in [0,-1]:
               depData["arcs"].append({
                  "start": min(word.id-1+lastWord, word.head+lastWord), 
                  "end": max(word.id-1+lastWord, word.head+lastWord), 
                  "label": word.deprel, "dir": "left" if word.head > word.id-1 else "right"})
         lastWord += len(sentence.words)
      html = displacy.render(depData, style="dep",
                  manual=True, page=True, minify=True)
      
      with open("../data/" + str(i)+"-"+jsonData[i]["name"]+".html", "w") as outputFile:
         outputFile.write(html)
         outputFile.close

      i += 1
