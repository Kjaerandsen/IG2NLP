import stanza
from utility import convertWordFormat
import json
from flask import Flask, request, Response
from utility import loadEnvironmentVariables

# Run this program with the following command:
# flask --app .\restPipeline.py run -p 5000
# The -p parameter sets the port of the webserver, if changed the environment variable
# "IG2FLASKURL" should also be changed accordingly.

def initialize():
    env = loadEnvironmentVariables()
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

@app.route('/', methods = ['GET', 'POST'])
def handleSingle():
    reqData = request.get_json()

    textDocs=[]
    i=0

    reqLen = len(reqData)
    while i < reqLen:
        textDocs.append(reqData[i]['baseTx'])
        i += 1

    data = []

    if reqLen == 1:
        docs = [nlp(textDocs[0])]
    elif reqLen == 0:
        return 'Invalid input', 400
    else:
        docs = nlp.bulk_process(textDocs)

    i = 0
    while i < len(docs):
        words = convertWordFormat(docs[i].sentences[0].words)
        data.append([word.__dict__ for word in words])
        i+=1

    response = Response(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    
    return response