from nlp.nlpUtility import *
from utility import *
from logic.matchingFunction import matchingHandler
import stanza

def initializePipeline(useGPU:bool, useCoref:bool,
                       dlMethod, logLevel, envPackage) -> stanza.Pipeline:
   """Initialize a Stanza nlp pipeline for future use"""

   processors = PROCESSORS
   if useCoref:
      processors.append('coref')

   pipeline = stanza.Pipeline(lang='en', use_gpu=useGPU, 
   processors=processors, 
   package=envPackage,
   download_method=dlMethod,
   logging_level=logLevel)

   return pipeline

def nlpPipelineMulti(pipeline:stanza.Pipeline, textDocs:list) -> list[stanza.Document]:
   """Takes a list of sentences as strings, returns the nlp pipeline results for the sentences"""
   logger.debug("Running multiple statement pipeline")
   docs = pipeline.bulk_process(textDocs)
   logger.debug("Finished running multiple statement pipeline")
   return docs
   
def nlpPipeline(pipeline:stanza.Pipeline, textDoc:str) -> list[stanza.Document]:
   """Takes a sentence as a string, returns the nlp pipeline results for the sentence"""
   logger.debug("Running single statement pipeline")
   doc = pipeline.process(textDoc)
   logger.debug("Finished running single statement pipeline")
   return doc

def processStatement(args:dict, statement:str, nlp:stanza.Pipeline) -> tuple[str,str]|str:
   try:
      doc = nlpPipeline(nlp, statement)
   except:

      return "","", "Error: Pipeline failed running the statement."
   words:list[Word]=[]
   outputConst = ""
   outputReg = ""

   """
   if "constitutive" in args:
      output = ""
      if args["constitutive"] == True:
         constitutive = True
      else:
         constitutive = False
      
      for sentence in doc:
         output += matchingHandler(convertWordFormat(sentence.words), False, constitutive)
      
      if constitutive:
         outputConst = output  
      else: 
         outputReg = output
   else:
   """
   outputConst = ""
   outputReg = ""

   for sentence in doc.sentences:
      words = convertWordFormat(sentence.words)
      outputConst += matchingHandler(copy.deepcopy(words), False, True, args)
      outputReg += matchingHandler(words, False, False, args)
   return outputConst, outputReg, ""