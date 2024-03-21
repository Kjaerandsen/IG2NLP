from utility import env
import json
from flask import Flask, request, Response, jsonify
from http import HTTPStatus
from nlp import *
import waitress
import logging

# Run this program with a development server using
# the following command:
# flask --app .\api.py run -p 5000
# The -p parameter sets the port of the webserver, if changed 
# the environment variable "IG2FLASKURL" should also be changed accordingly.

def initialize() -> None:   
   global nlp
   nlp = initializePipeline(
      env['useGPU'], env['coref'], env['downloadMethod'], env['logLevel'], env['pipeline'])
   print("Finished initializing")

initialize()
wlogger = logging.getLogger('waitress')
wlogger.setLevel(logging.WARNING)
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
                              "stmtId":statement["stmtId"],
                              "origStmt":statement["origStmt"],
                              #"encodedStmt":"Some modified data",
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
      # and potentially the api version, for reusing pipeline data if the same pipeline is utilized
        
   for i in range(len(responseData)):
      data = responseData[i]
      # Check the parameters and include all valid parameters
      params = {}
      for key in ["coref","semantic","semanticNumber"]:
         if key in data["matchingParams"]:
            # Validate as a boolean value
            if type(data["matchingParams"][key]) == bool:
               params[key] = data["matchingParams"][key]
            else:
               # Default to false if 
               params[key] = False
      # Append a full stop (.) to the input text if it does not end with one
      if data["origStmt"][-1] != ".":
         data["origStmt"] += "."

      #print(["origStmt"], data["origStmt"][-1])
      data["matchingParams"] = params
      # Run the nlp pipeline and matcher on the input statement(s)
      const, reg = processStatement(data["matchingParams"],data["origStmt"],nlp)
      data["econdedStmtReg"] = reg
      data["encodedStmtConst"] = const

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

if __name__ == "__main__":
   waitress.serve(app, host="0.0.0.0", port=env['flaskPort'])