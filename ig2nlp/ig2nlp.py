import json
import stanza
import argparse
#from stanza.models.common.doc import Sentence
#from copy import deepcopy

from logic.matchingFunction import matchingHandler
from logic.matchingFunctionConstitutive import matchingHandlerConstitutive
from logic.matchingFunctionShared import parseAndCompare
from utility.utility import *
from logic.classifier import *

semanticAnnotations = False

def main() -> None:
   parser = argparse.ArgumentParser()
   parser.add_argument("id", 
      help="Id from the input to run through the parser, -1 goes through all statements",
      default=-1, nargs='?', type=int)
   parser.add_argument("-i", "--input", 
      help="input file, defaults to json extension, i.e. input is treated as input.json",
      default="input")
   parser.add_argument("-s", "--single", 
      help="single mode, run one at a time instead of batching the nlp pipeline.", 
      action="store_true")
   parser.add_argument("-c","--constitutive", 
      help="Run the annotator in constitutive statement mode",
      action="store_true")
   parser.add_argument("-r","--reuse", 
      help="Run the annotator using cached items",
      action="store_true")
   parser.add_argument("-b", "--batch", 
      help="Batch size for the nlp pipeline. Lower values require less memory,"+
      " recommended values between 10 and 30, 0 batches everything. Default 30.",
      default=30, type=int)
   parser.add_argument("-o","--output", 
      help="output file, defaults to json extension, i.e. output is treated as output.json")
   args = parser.parse_args()

   i = args.id

   filename:str = "../data/"+args.input+".json"

   if args.output:
      outfilename:str = "../data/"+args.output+".json"
   else:
      outfilename:str = filename

   batchSize = int(args.batch)

   # The testData.json is a json file containing an array of objects 
   # with a name, baseText and processedText.
   # The important fields are the baseText which is the input statement 
   # and the processedText which is the annotated statement.
   with open(filename, "r") as input:
      jsonData = json.load(input)

   if not args.reuse:
      # If argument is -1 then go through all the items
      if i == -1:
         jsonData: list = MatcherMiddleware(jsonData, args.constitutive, args.single, batchSize)

      # Else only go through the selected item
      else:
         #print(jsonData[i]['baseText'])
         if i >= len(jsonData):
            print("Error, the index provided is higher than "+
               "or equal to the amount of items in the input data.")
         else:
            jsonData[i] = MatcherMiddleware(
               jsonData[i:i+1], args.constitutive, args.single, batchSize)[0]

   # Use cache version
   else:

      if i == -1:
         jsonData = cacheMatcher(jsonData, args.constitutive)
      else:
         #print(jsonData[i]['baseText'])
         if i >= len(jsonData):
            print("Error, the index provided is higher than "+
               "or equal to the amount of items in the input data.")
         else:
            jsonData[i] = cacheMatcher(
               jsonData[i:i+1], args.constitutive)[0]
         
   # Write the automatically parsed statement(s) to the file
   with open(outfilename, "w") as outputFile:
      json.dump(jsonData, outputFile, indent=2)



def MatcherMiddleware(jsonData:list, constitutive:bool, singleMode:bool, batchSize:int) -> list:
   """Initializes the nlp pipeline globally to reuse the pipeline across the
      statements and runs through all included statements."""

   global flaskURL
   global env

   jsonLen = len(jsonData)
   logger.info("\nRunning runnerAdvanced with "+ str(jsonLen) + " items.")

   logger.info("Loading nlp pipeline")
   global nlp
   nlp = stanza.Pipeline('en', use_gpu=env['useGPU'],
                  processors='tokenize,lemma,pos,depparse, mwt, ner, coref',
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
   logger.info("Finished loading the nlp pipeline")

   # Delete the environment variables dictionary
   del env

   textDocs:list[str]=[]
   for jsonObject in jsonData:
      textDocs.append(jsonObject['baseTx'])

   if singleMode:
      docs:list[stanza.Document]=[]
      for sentence in textDocs:
         docs.append(nlpPipeline(sentence))
   else:
      if batchSize == 0:
         docs = nlpPipelineMulti(textDocs)
      else:
         docs=[]
         # Go through the nlp pipeline in batches of batchSize
         while len(textDocs) > batchSize:
            pipelineResults = nlpPipelineMulti(textDocs[:batchSize])
            for doc in pipelineResults: docs.append(doc)
            textDocs = textDocs[batchSize:]
         # Add the remaining items
         pipelineResults = nlpPipelineMulti(textDocs)
         for doc in pipelineResults: docs.append(doc)

   for i, doc in enumerate(docs):
      print("\nStatement", str(i) + ": " + jsonData[i]['name'])
      logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'])
      words:list[Word]=[]
      #words = doc.sentences
      #print(len(doc.sentences))
      for j in range(len(doc.sentences)):
         #for word in doc.sentences[j].words:
         #   print(word.text)
         words.append(convertWordFormat(doc.sentences[j].words))
         #for word in words[0]:
            #print(word.text)

      if constitutive:
         output = matchingHandlerConstitutive(words[0], semanticAnnotations)
         if len(words) > 1:
            for sentence in words[1:]:
               output += " " + matchingHandlerConstitutive(sentence, semanticAnnotations)
      else:
         output = matchingHandler(words[0], semanticAnnotations)
         if len(words) > 1:
            for sentence in words[1:]:
               output += " " + matchingHandler(sentence, semanticAnnotations)

      #print(jsonData[i]['baseTx'] + "\n" + jsonData[i]['manuTx'] + "\n" + output)
      logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'] + " finished processing.")
      jsonData[i]["autoTx"] = output

   logger.info("Finished running matcher\n\n")
   return jsonData

def cacheMatcher(jsonData:list, constitutive:bool) -> list:
   """Initializes the nlp pipeline globally to reuse the pipeline across the
      statements and runs through all included statements."""
   global env

   jsonLen = len(jsonData)
   logger.info("\nRunning runnerAdvanced with "+ str(jsonLen) + " items.")

   # Delete the environment variables dictionary
   del env

   docs=[]
   print(len(jsonData))
   for jsonObject in jsonData:
      # Read contents of the cache file
      fileName = "../data/cache/" + jsonObject['name'] + ".json"
      with open(fileName, "r") as file:
         data = json.load(file)
      
      sentences = []
      for sentence in data:
         wordList:list[Word] = []
         for word in sentence:
            wordList.append(wordFromDict(word))
         sentences.append(wordList)
      # Convert to DOC
      #doc = stanza.Document.from_serialized(data)
      # Append to docs
      docs.append(sentences)
   
   print(len(docs))
   
   for i, doc in enumerate(docs):
      print("\nStatement", str(i) + ": " + jsonData[i]['name'])
      logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'])
      
      '''
      print(classifier(doc[0]))
      if len(doc) > 1:
         for sentence in doc[1:]:
            print(classifier(sentence))

      '''
      if constitutive:
         #docBak = copy.deepcopy(doc[0])
         output = matchingHandlerConstitutive(doc[0], semanticAnnotations)
         #outputComp = matchingHandler(docBak, semanticAnnotations)
         #reg, const = parseAndCompare(doc[0], semanticAnnotations)
         #output = const
         if len(doc) > 1:
            for sentence in doc[1:]:
               #output += " " + parseAndCompare(sentence, semanticAnnotations)
               #sentenceBak = copy.deepcopy(sentence)
               output += " " + matchingHandlerConstitutive(sentence, 
                                                           semanticAnnotations)
               #outputComp += " " + matchingHandler(sentenceBak, semanticAnnotations)
         #print(output)
         #print(outputComp)

      else:
         output = matchingHandler(doc[0], semanticAnnotations)
         if len(doc) > 1:
            for sentence in doc[1:]:
               output += " " + matchingHandler(sentence, semanticAnnotations)

      print(jsonData[i]['baseTx'])
      #print(jsonData[i]['baseTx'] + "\n" + jsonData[i]['manuTx'] + "\n" + output)
      logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'] + " finished processing.")
      jsonData[i]["autoTx"] = output
      
   logger.info("Finished running matcher\n\n")
   return jsonData

def nlpPipelineMulti(textDocs:list) -> list[stanza.Document]:
   """Takes a list of sentences as strings, returns the nlp pipeline results for the sentences"""
   logger.debug("Running multiple statement pipeline")
   docs = nlp.bulk_process(textDocs)
   logger.debug("Finished running multiple statement pipeline")
   return docs
   
def nlpPipeline(textDoc:str) -> list[stanza.Document]:
   """Takes a sentence as a string, returns the nlp pipeline results for the sentence"""
   logger.debug("Running single statement pipeline")
   doc = nlp.process(textDoc)
   logger.debug("Finished running single statement pipeline")
   return doc

# Run the main function
main()