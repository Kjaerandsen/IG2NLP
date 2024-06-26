import json
from utility import *
from nlp import initializePipeline, nlpPipeline, nlpPipelineMulti
import argparse

semanticAnnotations = False

def main() -> None:
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

   # The testData.json is a json file containing an array of objects 
   # with a name, baseText and processedText.
   # The important fields are the baseText which is the input statement 
   # and the processedText which is the annotated statement.
   with open(filename, "r") as input:
      jsonData = json.load(input)

   # If argument is -1 then go through all the items
   if i == -1:
      jsonData = MatcherMiddleware(jsonData, args.single, batchSize)

   # Else only go through the selected item
   else:
      #print(jsonData[i]['baseText'])
      if i >= len(jsonData):
         print("Error, the index provided is higher than "+
            "or equal to the amount of items in the input data.")
      else:
         MatcherMiddleware(
            jsonData[i:i+1], args.single, batchSize)[0]


def MatcherMiddleware(jsonData:list, singleMode:bool, batchSize:int) -> None:
   """Initializes the nlp pipeline globally to reuse the pipeline across the
      statements and runs through all included statements."""
   global env

   jsonLen = len(jsonData)
   logger.info("\nRunning cache with "+ str(jsonLen) + " items.")

   logger.info("Loading nlp pipeline")
   global nlp 
   nlp = initializePipeline(
      env['useGPU'], env['coref'], env['downloadMethod'], env['logLevel'], env['pipeline'])

   logger.info("Finished loading the nlp pipeline")

   # Delete the environment variables dictionary
   del env

   textDocs=[]
   for jsonObject in jsonData:
      textDocs.append(jsonObject['baseTx'])

   if singleMode:
      docs=[]
      for sentence in textDocs:
         docs.append(nlpPipeline(nlp, sentence))
   else:
      if batchSize == 0:
         docs = nlpPipelineMulti(nlp, textDocs)
      else:
         docs=[]
         # Go through the nlp pipeline in batches of batchSize
         while len(textDocs) > batchSize:
            pipelineResults = nlpPipelineMulti(nlp, textDocs[:batchSize])
            for doc in pipelineResults: docs.append(doc)
            textDocs = textDocs[batchSize:]
         # Add the remaining items
         pipelineResults = nlpPipelineMulti(nlp, textDocs)
         for doc in pipelineResults: docs.append(doc)

   for i, doc in enumerate(docs):
      print("\nStatement", str(i) + ": " + jsonData[i]['name'])
      outFile = "../data/cache/" + jsonData[i]['name'] + ".json"
      wordLists:list[list[Word]]=[]
      for j in range(len(doc.sentences)):
         wordLists.append(convertWordFormat(doc.sentences[j].words))
      
      outList = []
      for words in wordLists:
         jsonWords = []
         for word in words:
            jsonWords.append(word.toJSON())
         outList.append(jsonWords)

      # Write the automatically parsed statement(s) to the file
      with open(outFile, "w") as outputFile:
         outputFile.write(json.dumps(outList, indent=4))
      #print(jsonData[i]['baseTx'] + "\n" + jsonData[i]['manuTx'] + "\n" + output)
      logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'] + " finished writing to file.")
      i+=1


# Run the main function
main()