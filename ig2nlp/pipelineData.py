import json
import stanza
import pandas as pd

from utility import env, compoundWordsHandler

filename = "../data/input.json"

pd.set_option('display.max_rows', None)
pd.set_option('display.width', 200)

nlp = stanza.Pipeline('en', use_gpu=env['useGPU'], 
   processors='tokenize,pos,lemma,depparse,ner,coref,mwt', 
   package={"ner": ["ontonotes_charlm"]},
   download_method=env['downloadMethod'],
   logging_level=env['logLevel'])

nlp2 = stanza.Pipeline('en', use_gpu=env['useGPU'], 
   processors='tokenize,pos,lemma,ner,mwt', 
   package={"ner": ["conll03_charlm"]},
   download_method=env['downloadMethod'],
   logging_level=env['logLevel'])

nlp3 = stanza.Pipeline('en', use_gpu=env['useGPU'], 
   processors='tokenize,pos,lemma,ner,mwt', 
   package={"ner": ["ontonotes-ww-multi_nocharlm"]},
   download_method=env['downloadMethod'],
   logging_level=env['logLevel'])


nlp4 = stanza.Pipeline('en', use_gpu=env['useGPU'], 
   processors='tokenize,pos,lemma,ner,mwt', 
   package={"ner": ["ontonotes-ww-multi_charlm"]},
   download_method=env['downloadMethod'],
   logging_level=env['logLevel'])

# Delete the environment variables dictionary
del env

with open(filename, "r") as input:
   
   jsonData = json.load(input)

   i = 0

   print("Running with ", len(jsonData), " items.")

   with open("../data/pipeline.txt", "w") as outputFile:
   
      textDocs = []
      while i < len(jsonData): 
         textDocs.append(jsonData[i]['baseTx'])
         i+=1

      docs = nlp.bulk_process(textDocs)
      docs2 = nlp2.bulk_process(textDocs)
      docs3 = nlp3.bulk_process(textDocs)
      docs4 = nlp4.bulk_process(textDocs)

      i = 0
      while i < len(docs):
         doc = docs[i]
         doc2 = docs2[i]
         doc3 = docs3[i]
         doc4 = docs4[i]
         
         print(doc.text)
         outputFile.write("Name: "+ str(i)+"-"+jsonData[i]['name']+ "\n")
         outputFile.write(jsonData[i]['baseTx']+ "\n")
         # Based on the example found at: 
# https://stanfordnlp.github.io/stanza/depparse.html#accessing-syntactic-dependency-information
         j = 0
         while j < len(doc.sentences):
            sentence = doc.sentences[j]
            sentence2 = doc2.sentences[j]
            sentence3 = doc3.sentences[j]
            sentence4 = doc4.sentences[j]
            sentence.words = compoundWordsHandler(sentence.words)
            sentence2.words = compoundWordsHandler(sentence2.words)
            # Generating the data structure for displacy visualization
            df = pd.DataFrame(columns=["Word", "POS", "XPOS", "Head id", "Head word", 
                                    "Dependency", "Lemma", "Feats", "COREF"])
            for word in sentence.words:
               df = df._append({
                  "Word": word.text, "POS":word.pos, "XPOS":word.xpos, "Head id":word.head, 
                  "Head word":(sentence.words[word.head-1].text if word.head > 0 
                            else "root"), 
                  "Dependency": word.deprel, "Lemma": word.lemma, 
                  "Feats":word.feats, 
                  "COREF": word.coref_chains[0].chain.representative_text 
                  if word.coref_chains!=None and len(word.coref_chains) > 0
                  else ""}, 
                  ignore_index=True)
            outputFile.write("\nWords:\n")
            outputFile.write(str(df))
            df = pd.DataFrame(columns=["Token", "POS", "XPOS", "Head id", 
                                 "Dependency", "NER", "NER2", "NER3"])
            k = 0
            while k < len(sentence.tokens):
               token = sentence.tokens[k]
               df = df._append({
                  "Token": token.text, "POS":token.words[0].pos, "XPOS":token.words[0].xpos, 
                  "Head id":token.words[0].head,  
                  "Dependency": token.words[0].deprel, 
                  "NER": token.ner, "NER2": sentence2.tokens[k].ner,
                  "NER3": sentence3.tokens[k].ner,
                  "NER4": sentence4.tokens[k].ner}, ignore_index=True)
               k+=1
            outputFile.write("\nTokens:\n")
            outputFile.write(str(df))
            outputFile.write("\n\n")
            j+=1

         i += 1
   outputFile.close
