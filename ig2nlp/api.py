import werkzeug
from utility import env
import json
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
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
CORS(app)

@app.post("/ig2nlp")
def handleRequest() -> Response:
   data:dict = request.json
   
   responseData = []
   for i in range(len(data)):
      statement = data[i]
      
      """ Data validation """
      if not "apiVersion" in statement:
         return createError("Missing apiVersion parameter, please supply a valid apiVersion (0.1)", 
                              HTTPStatus.BAD_REQUEST)
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
                              statement["matchingParams"] if "matchingParams" in statement 
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
      const, reg, commentConst, commentReg = processStatement(
         data["matchingParams"],data["origStmt"],nlp)
      data["encodedStmtReg"] = reg
      data["encodedStmtConst"] = const
      data["commentReg"] = commentReg
      data["commentConst"] = commentConst

   return(jsonify(responseData))

@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e) -> Response:
   return createError("Bad request, please refer to the documentation for details on the expected "+
                      "JSON structure for input data.",400)

@app.errorhandler(werkzeug.exceptions.NotFound)
def handle_not_found(e) -> Response:
   return createError("Endpoint or resource requested was not found on the server. " +
                     'The default endpoint is "ig2nlp". ' +
                     "For a list of valid endpoints please refer to the documentation.",404)

@app.errorhandler(werkzeug.exceptions.UnsupportedMediaType)
def handle_unsupported_media_type(e) -> Response:
   return createError('The endpoint expects JSON data, but the provided Content-Type was not ' +
                      '"application/json"',415)

@app.errorhandler(werkzeug.exceptions.MethodNotAllowed)
def handle_method_not_allowed(e) -> Response:
   return createError("Method not allowed, for the ig2nlp endpoint a POST request with a JSON body"+
                     " as defined in the documentation is expected.", 405)

@app.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_internal_server_error(e) -> Response:
   return createError("Internal Server Error",500)

def createError(msg:str, type:int) -> Response:
   response = Response(
      response=json.dumps({"error":msg}),
      status=type,
      mimetype='application/json'
   )

   return response

if __name__ == "__main__":
   waitress.serve(app, host="0.0.0.0", port=env['flaskPort'])