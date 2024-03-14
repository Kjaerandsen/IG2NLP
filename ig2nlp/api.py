from utility import env
import json
from flask import Flask, request, Response, jsonify
from http import HTTPStatus
from nlp import *
from logic import matchingFunction

# Run this program with a development server using
# the following command:
# flask --app .\api.py run -p 5000
# The -p parameter sets the port of the webserver, if changed 
# the environment variable "IG2FLASKURL" should also be changed accordingly.

def initialize() -> None:
   config = pipelineConfig(tokenize="combined",
                           mwt="combined",
                           pos="combined_electra-large",
                           depparse="combined_electra-large",
                           lemma="combined_charlm",
                           ner="ontonotes-ww-multi_charlm",
                           coref="ontonotes_electra-large")
   global nlp
   nlp = initializePipeline(
      config, env['useGPU'], env['downloadMethod'], env['logLevel'])
   print("Finished initializing")

initialize()
app = Flask(__name__)

@app.post("/ig2nlp")
def handleRequest() -> Response:
   data:dict = request.json
   
   responseData = []
   for i in range(len(data)):
      statement = data[i]
      
      """ Data validation """
      if statement["apiVersion"] != 0.1:
         statement["apiVersion"] = float(statement["apiVersion"])
         if statement["apiVersion"] != 0.1:
            return createError("Invalid api version, please supply a valid apiVersion (0.1)", 
                              HTTPStatus.BAD_REQUEST)


      
      """ Data processing """
      try:
         responseData.append({
                              "stmdId":statement["stmtId"],
                              "origStmt":statement["origStmt"],
                              "encodedStmt":"Some modified data",
                              "apiVersion":statement["apiVersion"],
                              "matchingParams": 
                              statement["matchingParams"] if statement["matchingParams"] 
                              else {}
                           })
      except:
         return createError("Invalid input data, please refer to documentation "\
                            "for JSON structure information", 
                           HTTPStatus.BAD_REQUEST)
      
   # TODO: potentially add a middlware with caching functionality, use a hash of the statement text
      # and potentially the api version, for reuse if the same pipeline is utilized
        
   for i in range(len(responseData)):
      data = responseData[i]
      const, reg = processStatement(data["matchingParams"],data["origStmt"],nlp)
      data["encodedStmt"] = reg + const

   return(jsonify(responseData))


"""   
@app.route('/')
def handleRequest() -> Response:
   args = request.args

   if len(args) == 0:
      return createError("No parameters provided", HTTPStatus.BAD_REQUEST)
   #for arg in args:
   #   print(arg)
   statement = args.get("statement")
   statementType = args.get("statementType")
   coref = args.get("coref")
   semantic = args.get("semantic")
   semanticQuantity = args.get("semanticQuantity")

   if statement == None:
      return createError("No statement query parameter provided", HTTPStatus.BAD_REQUEST)

   print(args.get("statement"))
   # Argument validation
   # Max chars?

   # Constitutive / Regulative

   # Coreference resolution

   # Combine property and component

   # Semantic annotations (Date / Quantity / Entity)

   # Statement input validation / formatting
   return createError("Not found", HTTPStatus.BAD_REQUEST)
"""

def createError(msg:str, type:int) -> Response:
   response = Response(
      response=json.dumps({"error":msg}),
      status=type,
      mimetype='application/json'
   )

   return response