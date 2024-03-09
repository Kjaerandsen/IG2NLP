import json
import stanza
from utility import env

filename = "../data/input.json"

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

nlp2 = stanza.Pipeline('en', use_gpu=env['useGPU'],
   processors='tokenize,pos,lemma,depparse,ner,mwt', 
   package={
      "tokenize": "combined",
      "mwt": "combined",
      "pos": "combined_electra-large",
      "depparse": "combined_charlm",
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

   docs = nlp.bulk_process(textDocs)
   docs2 = nlp2.bulk_process(textDocs)

   i = 0
   while i < len(docs):
      print(jsonData[i]['name'])
      doc = docs[i]
      doc2 = docs2[i]

      j = 0
      while j < len(doc.sentences):
         sentence = doc.sentences[j]
         sentence2 = doc2.sentences[j]

         k = 0
         while k < len(sentence.words):
            word1 = sentence.words[k]
            word2 = sentence2.words[k]

            if word1.deprel != word2.deprel:
               print("Different deprels:\n", word1.text, word1.deprel, "\n", 
                    word2.text, word2.deprel)
            if sentence2.words[word1.head-1].text != sentence2.words[word2.head-1].text:
               print("Different head text:\n", word1.text, sentence.words[word1.head-1].text, 
                    "\n", word2.text, sentence2.words[word2.head-1].text)
               
            k+=1
         j+=1
      i += 1
