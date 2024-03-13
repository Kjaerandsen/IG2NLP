import stanza
from utility import env
import json
from flask import Flask, request, Response
from http import HTTPStatus


# Run this program with the following command:
# flask --app .\api.py run -p 5000
# The -p parameter sets the port of the webserver, if changed the environment variable
# "IG2FLASKURL" should also be changed accordingly.

def initialize() -> None:
   global nlp
   nlp = stanza.Pipeline('en', use_gpu=env['useGPU'],
      processors='tokenize,lemma,pos,depparse, mwt, ner, coref',
      package={
         "tokenize": "combined",
         "mwt": "combined",
         "pos": "combined_electra-large",
         "depparse": "combined_electra-large",
         "lemma": "combined_charlm",
         "ner": "ontonotes-ww-multi_charlm",
      },
      download_method=env['downloadMethod'],
      logging_level=env['logLevel']
      )
   print("Finished initializing")

initialize()
app = Flask(__name__)

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
   

def createError(msg:str, type:int) -> Response:
   response = Response(
      response=json.dumps({"error":msg}),
      status=type,
      mimetype='application/json'
   )

   return response