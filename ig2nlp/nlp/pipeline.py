from nlp.nlpUtility import *
from utility import *
import stanza

def initializePipeline(config:pipelineConfig, useGPU:bool, dlMethod, logLevel) -> stanza.Pipeline:
   """Initialize a Stanza nlp pipeline for future use"""

   pipeline = stanza.Pipeline(lang='en', use_gpu=useGPU, 
   processors=config.getProcessors(), 
   package=config.getPackage(),
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