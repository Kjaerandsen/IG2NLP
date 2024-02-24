import json
import stanza
import requests
from matchingFunction import *
from utility import *
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("id", 
        help="Id from the input to run through the parser, -1 goes through all statements")
    parser.add_argument("-i", "--input", 
        help="input file, defaults to json extension, i.e. input is treated as input.json")
    args = parser.parse_args()

    number = int(args.id)

    if not args.input:
        filename = "../data/input.json"
    else:
        filename = "../data/"+args.input+".json"

    i = number

    # The testData.json is a json file containing an array of objects 
    # with a name, baseText and processedText.
    # The important fields are the baseText which is the input statement 
    # and the processedText which is the annotated statement.
    with open(filename, "r") as input:
        jsonData = json.load(input)

    # If argument is -1 then go through all the items
    if i == -1:
        i = 0

        print("Running with ", len(jsonData), " items.")
        
        jsonData = MatcherMiddleware(jsonData)

        # Write the automatically parsed statement to the file
        with open(filename, "w") as outputFile:
            json.dump(jsonData, outputFile, indent=2)

    # Else only go through the selected item
    else:
        #print(jsonData[i]['baseText'])
        if i >= len(jsonData):
            print("Error, the index provided is higher than "+
                "or equal to the amount of items in the input data.")
        else:
            jsonData[i] = MatcherMiddleware(jsonData[i:i+1])[0]

        # Write the automatically parsed statement to the file
        with open(filename, "w") as outputFile:
            json.dump(jsonData, outputFile, indent=2)
                
        #    i += 1



def MatcherMiddleware(jsonData:list) -> list:
    """Initializes the nlp pipeline globally to reuse the pipeline across the
       statements and runs through all included statements."""
    global useREST
    global flaskURL
    global env
    
    flaskURL = env['flaskURL']
    useREST = env['useREST']

    jsonLen = len(jsonData)
    logger.info("\nRunning runnerAdvanced with "+ str(jsonLen) + " items.")

    if not useREST or jsonLen != 1:
        logger.info("Loading nlp pipeline")
        global nlp
        useREST = False
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

    textDocs=[]
    for jsonObject in jsonData:
        textDocs.append(jsonObject['baseTx'])

    if useREST:
        docs = nlpPipelineMulti(jsonData)
    else:
        docs = nlpPipelineMulti(textDocs)

    for i, doc in enumerate(docs):
        print("\nStatement", str(i) + ": " + jsonData[i]['name'])
        logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'])
        if not useREST:
            words = doc.sentences[0].words
            words = convertWordFormat(words)
        else:
            words = doc

        output = matchingHandler(words)
        
        #print(jsonData[i]['baseTx'] + "\n" + jsonData[i]['manual'] + "\n" + output)
        logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'] + " finished processing.")
        jsonData[i]["stanza"] = output
        i+=1

    logger.info("Finished running matcher\n\n")
    return jsonData

def nlpPipelineMulti(textDocs:list) -> list:
    """Takes a list of sentences as strings, returns the nlp pipeline results for the sentences"""
    if not useREST:
        logger.debug("Running multiple statement pipeline")
        docs = nlp.bulk_process(textDocs)
        logger.debug("Finished running multiple statement pipeline")
        return docs
    else:
        response = requests.post(flaskURL, json = textDocs)
        responseJSON = response.json()

        docs:list = []
        # Convert the response json to words
        for sentence in responseJSON:
            sentenceWords:list[Word] = []
            for word in sentence:
                sentenceWords.append(
                    Word(
                        word['text'],
                        word['pos'],
                        word['deprel'],
                        word['head'],
                        word['id'],
                        word['lemma'],
                        word['xpos'],
                        word['feats'],
                        word['start'],
                        word['end'],
                        word['spaces'],
                        word['symbol'],
                        word['nested'],
                        word['position'],
                        word['ner'],
                        word['logical'],
                        word['corefid'],
                        word['coref'],
                        word['corefScope'],
                        word['isRepresentative']
                    )
                )
            docs.append(sentenceWords)
        return docs

# Run the main function
main()