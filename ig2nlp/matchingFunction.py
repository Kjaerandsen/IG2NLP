import stanza
import time
import copy
import requests
from utility import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1

# Middleware for the matcher, initializes the nlp pipeline globally to reuse the pipeline across the
# statements and runs through all included statements.
def MatcherMiddleware(jsonData):
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

    i = 0
    textDocs=[]
    while i < jsonLen:
        textDocs.append(jsonData[i]['baseTx'])
        i += 1

    if useREST:
        docs = nlpPipelineMulti(jsonData)
    else:
        docs = nlpPipelineMulti(textDocs)

    i = 0
    while i < len(docs):
        print("\nStatement", str(i) + ": " + jsonData[i]['name'])
        logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'])
        if not useREST:
            words = docs[i].sentences[0].words
            output = WordsToSentence(
            corefReplace(
                matchingFunction(
                    compoundWordsMiddleware(
                        words))))
        else:
            words = docs[i]
            output = WordsToSentence(
            corefReplace(
                matchingFunction(
                    compoundWordsMiddlewareWords(
                        words))))


        
        
        print(jsonData[i]['baseTx'] + "\n" + jsonData[i]['manual'] + "\n" + output)
        logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'] + " finished processing.")
        jsonData[i]["stanza"] = output
        i+=1

    logger.info("Finished running matcher\n\n")
    return jsonData

# Takes a sentence as a string, returns the nlp pipeline results for the string
def nlpPipeline(text):
    # Run the nlp pipeline on the input text
    logger.debug("Running single statement pipeline with statement: "+ text)
    if not useREST:
        doc = nlp(text)
        returnVal = doc.sentences[0].words
        logger.debug("Finished running single statement pipeline")
        return returnVal
    else:
        output = [{"baseTx":text}]
        returnVal = nlpPipelineMulti(output)[0]
        logger.debug("Finished running single statement pipeline")
        return returnVal

# Takes a list of sentences as strings, returns the nlp pipeline results for the sentences
def nlpPipelineMulti(textDocs):
    if not useREST:
        logger.debug("Running multiple statement pipeline")
        docs = nlp.bulk_process(textDocs)
        logger.debug("Finished running multiple statement pipeline")
        return docs
    else:
        #requestBody = []
        #for doc in textDocs:
        #    requestBody.append({"baseTx":str(doc)})
        #print(textDocs.keys())
        response = requests.post(flaskURL, json = textDocs)
        responseJSON = response.json()

        docs = []
        # Convert the response json to words
        for sentence in responseJSON:
            sentenceWords = []
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

# Matching function, takes a list of words with dependency parse and pos-tag data.
# Returns a list of words with IG Script notation symbols.
def matchingFunction(words):
    wordLen = len(words)
    wordsBak = copy.deepcopy(words)
    i = 0

    while i < wordLen:
        deprel = words[i].deprel

        # Print out more complex dependencies for future handling
        #if ":" in deprel:
        #    if deprel != "aux:pass" and deprel != "obl:tmod":
        #        print("\n", '":" dependency: ',words[i], "\n")

        #print(words[words[i].head-1], words[i].deprel, words[i].text)

        # (Cac, Cex) Condition detection 
        if deprel == "advcl":
            words2 = []
            if handleCondition(words, wordsBak, i, wordLen, words2):
                return words2

        # (O) Or else detection
        elif deprel == "cc" and words[i+1].text == "else":
            words2 = []
            orElseHandler(words, wordsBak, wordLen, words2, i)
            return words2

        # (Cex) Execution constraint detection
        elif deprel == "obl":
            # Check for connections to the obl both before and after
            scopeStart = i
            scopeEnd = i

            j = 0
            while j < wordLen:
                if words[j].head-1 == i and words[j].deprel != "punct":
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                #elif words[words[j].head-1].head-1 == i and words[j].deprel != "punct":
                #    if j > scopeEnd:
                #        scopeEnd = j
                #    elif j < scopeStart:
                #        scopeStart = j
                elif ifHeadRelation(words, j, i) and words[j].deprel != "punct":
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                j += 1
            
            if scopeEnd - scopeStart >= minimumCexLength:
                # Reconsider the two lines below in the future
                #if words[scopeStart].deprel == "case" and words[scopeStart+1].deprel == "det":
                #    scopeStart += 2
                # Look for symbols within
                '''
                j = scopeStart
                while j < scopeEnd:
                    if words[j].symbol != "":
                        print("\n\nNot none\n\n", words[j].symbol)
                    j += 1
                '''
                # Add the words as a Cex
                #print("Setting CEX", WordsToSentence(words[scopeStart:scopeEnd+1]))
                words[scopeStart].setSymbol("Cex", 1)
                words[scopeEnd].setSymbol("Cex", 2)
                if scopeEnd - scopeStart > 2:
                    words = findInternalLogicalOperators(words, scopeStart, scopeEnd)
            
            i = scopeEnd

        # Advmod of Aim is correlated with execution constraints
        # Might be too generic of a rule.
        elif deprel == "advmod" and words[words[i].head-1].symbol == "I":
            #print("\nadvmod connected to Aim(I): ", words[i])
            if i+1 < wordLen:
                if words[i+1].deprel == "punct":
                    words[i].setSymbol("Cex")

        # (Cex) Execution constraint detection 2
        elif deprel == "obl:tmod":
            i = words[i].head-1

            scopeStart = i
            scopeEnd = i

            j = 0

            while j < wordLen:
                if (words[j].head-1 == i 
                    and words[j].deprel != "punct" 
                    and words[j].deprel != "cc"):
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                elif (ifHeadRelation(words, j, i) 
                      and words[j].deprel != "punct"
                      and words[j].deprel != "cc"):
                    if j > scopeEnd:
                        scopeEnd = j
                    elif j < scopeStart:
                        scopeStart = j
                j += 1
            
            if scopeEnd - scopeStart != 0:
                # Reconsider the two lines below in the future
                #if words[scopeStart].deprel == "case" and words[scopeStart+1].deprel == "det":
                #    scopeStart += 2
                # Add the words as a Cex
                words[scopeStart].setSymbol("Cex", 1)
                words[scopeEnd].setSymbol("Cex", 2)
                if scopeEnd - scopeStart > 2:
                    words = findInternalLogicalOperators(words, scopeStart, scopeEnd)
            
            i = scopeEnd

        #elif deprel == "nmod" and words[words[i].head-1].symbol == "A":
            #print("\nnmod connected to Attribute(A): ", words[i])

        # (Bdir) Object detection
        elif deprel == "obj":
            iBak = i
            smallLogicalOperator(words, i, "Bdir", wordLen)
            # Positive lookahead for nmod to include:
            # May need future refinement
            '''
            if words[i].position == 0:
                j=i
                while j < wordLen:
                    if words[j].deprel == "nmod" and words[j].head-1 == i:
                        if j+1 < wordLen:
                            if not ifHeadRelation(words, j+1, j):
                                words[i].setSymbol("Bdir", 1)
                                words[j].setSymbol("Bdir", 2)
                                i = j
                            break
                        else:
                            words[i].setSymbol("Bdir", 1)
                            words[j].setSymbol("Bdir", 2)
                            i = j
                            break
                    j += 1
            '''

            # If the flag is True combine the object with single word properties preceeding 
            # the object
            if CombineObjandSingleWordProperty:
                if (words[iBak-1].symbol == "Bdir,p" and words[iBak-1].deprel == "amod"
                    and words[iBak-1].position == 0):
                    if (words[iBak-2].symbol != "Bdir,p"):
                        if iBak != i:
                            words[iBak].setSymbol("", 0)
                            words[iBak-1].setSymbol("Bdir", 1)
                        else:
                            words[iBak].setSymbol("Bdir", 2)
                            words[iBak-1].setSymbol("Bdir", 1)

        #elif deprel == "compound":
        #    i, error = compoundHandler(words, i)
        #    if error:
        #        logger.debug("compoundHandler returned True")
        #    else:
        #        logger.debug("compoundHandler returned False")

        # (Bind) Indirect object detection
        elif deprel == "iobj":
            iBak = i
            smallLogicalOperator(words, i, "Bind", wordLen)
            # If the flag is True combine the object with single word properties preceeding 
            # the object

            if CombineObjandSingleWordProperty:
                if (words[iBak-1].symbol == "Bind,p" and words[iBak-1].deprel == "amod"
                    and words[iBak-1].position == 0):
                    if iBak != i:
                        words[iBak].setSymbol("", 0)
                        words[iBak-1].setSymbol("Bind", 1)
                    else:
                        words[iBak].setSymbol("Bind", 2)
                        words[iBak-1].setSymbol("Bind", 1)


        # (I) Aim detection
        elif deprel == "root":
            # Potentially unmatch all occurences where the aim is not a verb
            #if words[i].pos != "VERB":
            #    print("Aim is not VERB:", words[i].pos, words[i])
            # Look for logical operators
            words[i].setSymbol("I")
            smallLogicalOperator(words, i, "I", wordLen, True)
            if words[i].position == 0:
                # Look for xcomp dependencies
                k = 0

                while k < wordLen:
                    if words[k].deprel == "xcomp" and words[k].head-1 == i:
                        #print("XComp of I: ", words[k], k, i)
                        # If the xcomp is adjacent encapsulate it in the aim component
                        if k-i == 2:
                            words[i].setSymbol("I",1)
                            words[i+2].setSymbol("I",2)
                            i = k
                            break
                        else:
                            j = i+1
                            while j < k-1:
                                if words[j].head-1 != k:
                                    # Add semantic annotation for context based on xcomp
                                    # if the xcomp is not adjacent to the aim
                                    words[i].text = (words[i].text + " " * words[k].spaces + "[" + 
                                                     words[k].text + "]")
                                    j = k
                                    break
                                j+=1
                            if j == k-1:
                                # If the xcomp is adjacent encapsulate it in the aim component
                                words[i].setSymbol("I",1)
                                words[k].setSymbol("I",2)
                                i = k
                            
                        
                    k += 1
                #print("Done with aim: ", WordsToSentence(words), "\n",words[i])
                #if wordLen > i+1:
                #    print(words[i+1])
            
        
        # Else if the word has an amod dependency type, check if the head is a symbol
        # that supports properties, if so, the word is a property of that symbol
        # (Bdir,p, Bind,p, A,p)
        elif words[i].deprel == "amod":
            # If the word is directly connected to an obj (Bdir)
            if words[words[i].head-1].deprel == "obj":
                smallLogicalOperator(words, i, "Bdir,p", wordLen)
                #words[i].setSymbol("Bdir,p")
            # Else if the word is directly connected to an iobj (Bind)
            elif words[words[i].head-1].deprel == "iobj":
                smallLogicalOperator(words, i, "Bind,p", wordLen)
                #words[i].setSymbol("Bind,p")
            # Else if the word is connected to a nsubj connected directly to root (Attribute)
            elif (words[words[i].head-1].deprel == "nsubj" 
                  and (words[words[words[i].head-1].head-1].deprel == "root" or 
                  words[words[words[i].head-1].head-1].symbol == "A")):
                smallLogicalOperator(words, i, "A,p", wordLen)
                #words[i].setSymbol("A,p")

        # (A,p) Attribute property detection 2
        elif words[i].deprel == "acl" and words[words[i].head-1].symbol == "A":
            words[i].setSymbol("A,p")

        # (Bdir,p) Direct object property detection 2
        elif words[i].deprel == "nmod:poss":
            if words[words[i].head-1].deprel == "obj" and words[i].head-1 == i+1:
                # Check if there is a previous amod connection and add both
                if words[i-1].deprel == "amod" and words[i-1].head-1 == i:
                    words[i-1].setSymbol("Bdir,p", 1)
                    words[i].setSymbol("Bdir,p", 2)
                # Else only add the Bdir,p
                else:
                    words[i].setSymbol("Bdir,p")
            #else:
                #print("\nWord is nmod:poss: ", words[i])
                    
        # (Bdir,p) Direct object property detection 3
        # TODO: Reconsider in the future if this is accurate enough
        # There are currently false positives, but they should be mitigated by better
        # Cex component detection
        elif (words[i].deprel == "acl" and words[words[i].head-1].symbol == "Bdir"
              and words[i-1].symbol == "Bdir"):
            words[i].setSymbol("Bdir,p")
        
        # (A) Attribute detection
        elif "nsubj" in deprel:
            if words[i].pos != "PRON":
                # Look for nmod connected to the word i
                j = 0

                other = False
                while j < wordLen:
                    if "nmod" in words[j].deprel and ifHeadRelation(words, j, i):
                        #print("A with xpos: ", words[j], words[j].xpos)
                        #print("Nmod head relation to a: ", words[j], words[i])
                        smallLogicalOperator(words, j, "A", wordLen)
                        other = True
                        if words[i+1].deprel == "appos" and words[i+1].head-1 == i:
                            if words[i].position == 2:
                                words[i].setSymbol("")
                                words[i+1].setSymbol("A",2)
                                i+=1
                            else:
                                words[i].setSymbol("A",1)
                                words[i+1].setSymbol("A",2)
                                i+=1
                    j+=1 
                if not other:
                    smallLogicalOperator(words, i, "A", wordLen)
                    if words[i+1].deprel == "appos" and words[i+1].head-1 == i:
                        if words[i].position == 2:
                            words[i].setSymbol("")
                            words[i+1].setSymbol("A",2)
                            i+=1
                        else:
                            words[i].setSymbol("A",1)
                            words[i+1].setSymbol("A",2)
                            i+=1
            # If the nsubj is a pronoun connected to root then handle it as an attribute
            # This may need to be reverted in the future if coreference resolution is used
            # in that case, the coreference resolution will be used to add the appropriate attribute
            elif words[words[i].head-1].deprel == "root":
                smallLogicalOperator(words, i, "A", wordLen)
                if words[i+1].deprel == "appos" and words[i+1].head-1 == i:
                    if words[i].position == 2:
                        words[i].setSymbol("")
                        words[i+1].setSymbol("A",2)
                        i+=1
                    else:
                        words[i].setSymbol("A",1)
                        words[i+1].setSymbol("A",2)
                        i+=1

            # (A,p) detection mechanism, might be too specific. 
            # Is overwritten by Aim (I) component in several cases
            if words[i+1].deprel == "advcl" and words[words[i+1].head-1].deprel == "root":
                #print("ADVCL")
                words[i+1].setSymbol("A,p")

         # If the relation is a ccomp then handle it as a direct object
            '''
        elif (words[i].deprel == "amod" 
              and words[words[i].head-1].deprel == "nsubj" 
              and words[words[words[i].head-1].head-1].deprel == "ccomp"):
            #print("\n\nAMOD NSUBJ OBJ\n\n")
            words[i].setSymbol(words[i],"bdir", 1)
            words[i+1].setSymbol(words[i+1],"bdir", 2)
            i += 1
            '''
        elif words[i].deprel == "nsubj" and words[words[i].head-1].deprel == "ccomp":
            logger.debug("NSUBJ CCOMP OBJ")

        # Too broad coverage in this case, detected instances which should be included in the main
        # object in some instances, an instance of an indirect object component, and several 
        # overlaps with execution constraints.
        elif (words[i].deprel == "nmod" and words[words[i].head-1].symbol == "Bdir" 
              and words[words[i].head-1].position in [0,2]):
            # positive lookahead
            firstIndex = i
            doubleNmod = False
            j = 0
            # Find and encapsulate any other nmods connected to the last detected nmod
            while j < wordLen:
                if words[j].deprel == "nmod" and words[j].head-1 == i:
                    lastIndex = j
                    doubleNmod = True
                    i = j
                j+=1
            
            # if two or more nmod dependencies are connected then treat it as a Bdir,p
            if doubleNmod:
                # Set the first word after the direct object component as the start of the component
                words[words[firstIndex].head].setSymbol("Bdir,p", 1)
                words[lastIndex].setSymbol("Bdir,p", 2)
                i = lastIndex
            else:
                # Set the first word after the direct object component as the start of the component
                if words[words[firstIndex].head-1].position == 0:
                    words[words[firstIndex].head-1].setSymbol("Bdir", 1)
                else:
                    words[words[firstIndex].head-1].setSymbol("", 0)
                words[i].setSymbol("Bdir", 2)
                
        # (D) Deontic detection
        elif words[words[i].head-1].deprel == "root":
            if "aux" in deprel:
                if words[words[i].head-1].pos == "VERB":
                    #print("Deontic: ", words[i].xpos) 
                    #Might be worth looking into deontics that do not have xpos of MD
                    # Combine two adjacent deontics if present.
                    if words[i-1].symbol == "D":
                        words[i-1].setSymbol("D",1)
                        words[i].setSymbol("D",2)
                    else:
                        if (words[i].head-1 - i) > 1:
                            words[i].setSymbol("D",1)
                            words[words[i].head-2].setSymbol("D",2)
                        else:
                            words[i].setSymbol("D")
                else:
                    logger.debug("Deontic, no verb")
        
        i += 1

    return words


# Validation function for nested components
# Sets a requirement of both an Aim (I) and an Attribute (A) detected for a component to 
# be regarded as nested.
def validateNested(words):
    wordLen = len(words)

    Aim = False
    Attribute = False

    i = 0
    while i < wordLen:
        if words[i].symbol == "A":
            Attribute = True
            if Aim:
                return True
        if words[i].symbol == "I":
            Aim = True
            if Attribute:
                return True
        i += 1
    return False

# Check if the word is connected to the headId through a head connection
def ifHeadRelation(words, wordId, headId):
    while words[words[wordId].head-1].deprel != "root":
        if words[wordId].deprel == "root":
            return False
        if words[wordId].head-1 == headId:
            return True
        wordId = words[wordId].head-1
    return False

# List of allowed head connections for the function below
allowedAimHeads = ["conj","cc","det","amod","advmod"]
# Check if the word is connected to the headId through a head connection, specifically for Aim (I)
def ifHeadRelationAim(words, wordId, headId):
    while words[words[wordId].head-1].deprel != "root":
        if words[wordId].head-1 == headId:
            return True
        if not words[words[wordId].head-1].deprel in allowedAimHeads:
            return False
        wordId = words[wordId].head-1
    # Exception for the case where the headId is the root
    if words[headId].deprel == "root":
        return True
    return False

# Finds and handles symbols with logical operators
def smallLogicalOperator(words, i, symbol, wordLen, aim=False):
    scopeStart = i  
    scopeEnd = i

    j=scopeStart+1
    # Locations (ids) of cc dependent words
    ccLocs = []
    # Locations (ids) of puncts
    punctLocs = []
    # Locations (ids) of determiners
    detLocs = []

    if aim:
        # Go through the word list and find the scope of the component
        while j < wordLen:
            if ifHeadRelationAim(words, j, i):
                scopeEnd, j = LogicalOperatorHelper(words[j], wordLen, scopeEnd, ccLocs, j)
            j += 1
    else:
        while j < wordLen:
            # Go through the word list and find the scope of the component
            if ifHeadRelation(words, j, i):
                scopeEnd, j = LogicalOperatorHelper(words[j], wordLen, scopeEnd, ccLocs, j)
            j += 1
        
    ccCount = len(ccLocs)

    # If the scope is larger than one word in length and there is a cc deprel in the scope (and/or)
    if scopeEnd - scopeStart != 0 and ccCount > 0:
        # Go through the scope, if a deprel other than conj, cc and det is found
        # then handle it as a single word component instead.
        j = scopeStart
        while j < scopeEnd:
            if words[j].deprel == "det":
                if j == scopeStart:
                    detLocs.append(j)
                elif words[j-1].deprel == "cc":
                    detLocs.append(j)
            # Remove additional puncts (i.e. "x, and y" -> "x and y")
            elif words[j].deprel == "punct" and words[j].text == ",":
                if words[j+1].deprel == "cc":
                    words[j].spaces = 0
                    words[j].text = ""
                # If the word is a punct connected to the conj, then it should be replaced by a
                        # logical operator
                elif words[words[j].head-1].deprel == "conj":
                    punctLocs.append(j)
            j += 1

        # Remove dets
        j = 0
        while j < len(detLocs):
            k = detLocs[j]
            words[k].spaces = 0
            words[k].text = ""
            j += 1

        words[scopeStart].setSymbol(symbol, 1)
        words[scopeEnd].setSymbol(symbol, 2)
        
        i = scopeEnd

        # If there is only one CC in the component
        if ccCount == 1:
            # Set the contents of the cc to be a logical operator
            words[ccLocs[0]].toLogical()

            # Turn all extra punct deprels into the same logical operator as above
            j = 0
            while j < len(punctLocs):
                words[punctLocs[j]].spaces += 1
                words[punctLocs[j]].text = words[ccLocs[0]].text
                j+=1

            i = scopeEnd
        else:
            # Go through the list of words, create lists of logical operator sequences
            ccLocs2 = []
            ccTypes = []
            orConj = False
            andConj = False

            ccLocs = ccLocs + punctLocs

            '''
                if words[cc].deprel == "cc":
                    words[cc].toLogical()
                    if words[cc].text == "[AND]":
                        ccLocs2.append(cc)
                        ccTypes.append(words[cc].text)
                        andConj = True
                    elif words[cc].text == "[OR]":
                        ccLocs2.append(cc)
                        ccTypes.append(words[cc].text)
                        orConj = True
                    else:
                        print("Error, unknown cc")
                        return
                elif words[cc].text == ",":
                    if cc+1 in ccLocs:
                        words[cc].text = ""
                    else:
                        currOperatorLoc = next(
                                    (i for i, val in enumerate(ccLocs) if val > cc), -1)
                        currOperatorLoc = ccLocs[currOperatorLoc]
                        words[cc].text = words[currOperatorLoc].text
                        words[cc].spaces = 1 
                        ccLocs2.append(cc)
                        ccTypes.append(words[currOperatorLoc].text)
            '''
            # Potentially replace the while below with the one above by replacing the two lists with
            # a single list of tuples and sorting as the list is created, or afterwards.

            j = scopeStart
            while j < scopeEnd+1:
                if words[j].text == ",":
                    if j+1 in ccLocs:
                        words[j].text = ""
                        if j in punctLocs: punctLocs.remove(j)
                    else:
                        currOperatorLoc = next(
                            (i for i, val in enumerate(ccLocs) if val > j), -1)
                        # Set the currOperatorLoc to the value instead of the id
                        currOperatorLoc = ccLocs[currOperatorLoc]
                        if currOperatorLoc != -1:
                            words[currOperatorLoc].toLogical()
                            if words[currOperatorLoc].text == "[AND]":
                                ccLocs2.append(j)
                                ccTypes.append("AND")
                            elif words[currOperatorLoc].text == "[OR]":
                                ccLocs2.append(j)
                                ccTypes.append("OR")
                            else:
                                print("Error, unknown cc")
                                return
                            words[j].text = words[currOperatorLoc].text
                            words[j].spaces = 1
                        else:
                            logger.error(
                                "Error, punct not followed by a logical operator in logical"+
                                " operator handling.")
                elif words[j].deprel == "cc":
                    words[j].toLogical()
                    if words[j].text == "[AND]":
                        ccLocs2.append(j)
                        ccTypes.append("AND")
                        andConj = True
                    elif words[j].text == "[OR]":
                        ccLocs2.append(j)
                        ccTypes.append("OR")
                        orConj = True
                j+=1
            
            originalType = ccTypes[0]
            prevOperator = ccTypes[0]
            prevOperatorLoc = ccLocs2[0]
            # If there is a mix and match between symbol types handle the bracketing
            if andConj and orConj:
                logger.warning('Found both "and" and "or" logical operators in component, '+
                        "please review manually to solve potential encapsulation issues.")
                j = 0

                # Go through all the cc and handle the bracketing
                while j < len(ccLocs2):
                    nextLoc = ccLocs2[j]
                    nextType = ccTypes[j]

                    if prevOperator == originalType:
                        # If next operator is not then add the first word after the operator
                        # as the starting bracket
                        if nextType != originalType:
                            words[prevOperatorLoc+1].text = "(" + words[prevOperatorLoc+1].text
                    else:
                        # If previous is not original and this is then close the bracket
                        if nextType == originalType:
                            words[nextLoc-1].text += ")"
                    # Update the previous operator
                    prevOperator = nextType
                    prevOperatorLoc = nextLoc
                    j+=1

            # If the last operator is not the original add a closing bracket
            if ccTypes[len(ccLocs2)-1] != originalType:
                words[scopeEnd].text += ")"
            
            logger.warning("More than one CC in smallLogicalOperator function, " +
                             "please review logical operators")
    else:
        words[i].setSymbol(symbol)

def LogicalOperatorHelper(word, wordLen, scopeEnd, ccLocs, j):
    supported = ["punct","det","advmod","amod"]

    if word.deprel == "cc":
        ccLocs.append(j)
        scopeEnd = j
    elif word.deprel == "conj":
        scopeEnd = j
    # Also include advmod dependencies
    elif word.deprel == "advmod":
        scopeEnd = j
    # If the word is anything else than the supported components 
    # break the loop to not include further components
    elif not word.deprel in supported:
        j=wordLen-1
    
    return scopeEnd, j

# Handler function for the matching and encapsulation of conditions (Cac, Cex)
def handleCondition(words, wordsBak, i, wordLen, words2):
    firstVal = i
    
    # Go through the statement until the word is connected to the advcl directly or indirectly
    k = 0
    while k < i:
        # If connected to the advcl then set firstVal to the id and break the loop
        if ifHeadRelation(words, k, i):
            firstVal = k
            break
        k += 1

    # Go through again from the activation condition++
    # Until the word is no longer connected to the advcl
        
    # Set the lastVal to the current id -1    
    lastIndex = i+1
    k = i+1
    while k < wordLen:
        if not ifHeadRelation(words, k, i):
            lastIndex = k-1
            break
        k += 1

    if words[lastIndex].deprel != "punct":
        if words[lastIndex+1].deprel == "punct":
            lastIndex += 1
        else:
            logger.error("Last val in handleCondition was not punct" + words[lastIndex].text)
            #print("Last val was not punct", words[lastIndex])
            return False

    if firstVal == 0:
        contents = []

        '''
        if not useREST:
            condition = matchingFunction(
                compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[:lastIndex]))))
        else:
            condition = matchingFunction(
                compoundWordsMiddlewareWords(nlpPipeline(WordsToSentence(wordsBak[:lastIndex]))))
        '''
        #TODO: Test this further, the configuration above had a different outcome in one case
        condition = matchingFunction(reusePartSoS(wordsBak[:lastIndex], lastIndex))
        #actiWords = copy.deepcopy(words[:lastIndex])
        #Condition = matchingFunction(reusePart(actiWords, 0, lastIndex))

        j = 0
        oblCount = 0
        while j < len(condition):
            if "obl" in condition[j].deprel:
                oblCount+=1
            j+=1

        if oblCount > 1 and words[0].deprel == "mark":
            symbol = "Cex"
        else:
            symbol = "Cac"

        if validateNested(condition):
            words2.append(Word(
            "","","",0,0,"","","",0,0,0,symbol,True,1
            ))
            words2 += condition
            words2.append(Word("","","",0,0,"","","",0,0,0,symbol,True,2))
            words2.append(words[lastIndex])
        else:
            words2 += words[:lastIndex]
            words2[0].setSymbol(symbol,1)
            words2[lastIndex-1].setSymbol(symbol,2)
            words2.append(words[lastIndex])
            if lastIndex - firstVal > 2:
                words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)

        #contents = matchingFunction(compoundWordsMiddleware(nlpPipeline(
        #    WordsToSentence(words[lastIndex+1:]))))
        #contents = matchingFunction(reusePart(words[lastIndex+1:], lastIndex+1, 
        #                                            wordLen-(lastIndex+1)))
        contents = matchingFunction(reusePartEoS(words[lastIndex+1:], lastIndex+1))
        contents[0].spaces = 1

        # Copy over the old placement information to the 
        # newly generated words for proper formatting
        k = lastIndex +1
        while k < len(words):
            index = k-lastIndex-1
            contents[index].id = words[k].id
            contents[index].start = words[k].start
            contents[index].end = words[k].end
            contents[index].spaces = words[k].spaces

            k += 1

        # print("Contents are: '", contents[0].text, "'")
        words2 += contents

        return True
    elif words[firstVal].deprel == "mark":
        #print("First val was not id 0 and deprel was mark", words[lastIndex])
        # Do the same as above, but also with the words before this advcl
        contents = []

        '''
        if not useREST:
            # Add the values before the condition
            words2 += words[:firstVal]

            condition = matchingFunction(
                compoundWordsMiddleware(
                    nlpPipeline(WordsToSentence(wordsBak[firstVal:lastIndex]))))
        else:
            # Add the values before the condition
            words2 += words[:firstVal]

            condition = matchingFunction(
                compoundWordsMiddlewareWords(
                    nlpPipeline(WordsToSentence(wordsBak[firstVal:lastIndex]))))
        '''    
        # Add the values before the condition
        words2 += words[:firstVal]
        condition = matchingFunction(
                reusePartMoS(copy.deepcopy(wordsBak[firstVal:lastIndex]), firstVal, lastIndex))

        #actiWords = copy.deepcopy(words[:lastIndex])
        #Condition = matchingFunction(reusePart(actiWords, 0, lastIndex))
        j = 0
        oblCount = 0
        while j < len(condition):
            if "obl" in condition[j].deprel:
                oblCount+=1
            j+=1

        if oblCount > 1:
            symbol = "Cex"
        else:
            symbol = "Cac"

        if validateNested(condition):
            words2.append(Word(
            "","","",0,0,"","","",0,0,1,symbol,True,1
            ))
            condition[0].spaces = 0
            words2 += condition
            words2.append(Word("","","",0,0,"","","",0,0,0,symbol,True,2))
            words2.append(words[lastIndex])
        else:
            words2 += wordsBak[firstVal:lastIndex]
            words2[firstVal].setSymbol(symbol,1)
            words2[lastIndex-1].setSymbol(symbol,2)
            words2.append(words[lastIndex])
            if lastIndex - firstVal > 2:
                words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)

        #contents = matchingFunction(compoundWordsMiddleware(nlpPipeline(
        #    WordsToSentence(words[lastIndex+1:]))))
        #contents = matchingFunction(reusePart(words[lastIndex+1:], lastIndex+1, 
        #                                            wordLen-(lastIndex+1)))
        
        if wordLen > lastIndex+1:
            '''
            if not useREST:
                contents = matchingFunction(
                    compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[lastIndex+1:]))))
            else:
                contents = matchingFunction(
                    compoundWordsMiddlewareWords(nlpPipeline(
                        WordsToSentence(wordsBak[lastIndex+1:]))))
            '''
            lastPunct = False
            lastVal = wordLen
            if wordsBak[wordLen-1].deprel == "punct":
                lastPunct = True
                lastVal = wordLen-1
                wordLen -= 1        

            contents = matchingFunction(
                reusePartEoS(wordsBak[lastIndex+1:lastVal], lastIndex+1)
            )

            # Copy over the old placement information to the 
            # newly generated words for proper formatting
            k = lastIndex +1
            while k < wordLen:
                index = k-lastIndex-1
                contents[index].id = words[k].id
                contents[index].start = words[k].start
                contents[index].end = words[k].end
                contents[index].spaces = words[k].spaces

                k += 1

            # print("Contents are: '", contents[0].text, "'")
            words2 += contents
            if lastPunct:
                words2.append(wordsBak[lastVal])

        return True
    else:
        #print("First val was not id 0 and deprel was not mark", words[lastIndex])
        return False

# Handler function for the Or else (O) component
def orElseHandler(words, wordsBak, wordLen, words2, firstVal):
    # Include everything but the last punct if it exists    
    if words[wordLen-1].deprel == "punct":
        lastIndex = wordLen -1
    else:
        lastIndex = wordLen

    if not useREST:
        # Add the values before the condition
        words2 += words[:firstVal]

        #orElseComponent = matchingFunction(
        #    compoundWordsMiddleware(nlpPipeline(WordsToSentence(wordsBak[firstVal+2:lastIndex]))))
        orElseComponent = matchingFunction(
            reusePartEoS(wordsBak[firstVal+2:lastIndex], firstVal+2))
    else:
        # Add the values before the condition
        words2 += words[:firstVal]

        #orElseComponent = matchingFunction(
        #    compoundWordsMiddlewareWords(nlpPipeline(
        #        WordsToSentence(wordsBak[firstVal+2:lastIndex]))))
        orElseComponent = matchingFunction(
            reusePartEoS(wordsBak[firstVal+2:lastIndex], firstVal+2))

    words2.append(Word(
    "","","",0,0,"","","",0,0,1,"O",True,1
    ))
    words2 += orElseComponent
    words2.append(Word("","","",0,0,"","","",0,0,0,"O",True,2))
    # Append the last punct
    if words[wordLen-1].deprel == "punct":
        words2.append(words[wordLen-1])

def findInternalLogicalOperators(words, start, end):
    #print("Finding logical operators\n", start, end)
    j = start
    andCount = 0
    orCount = 0
    while j < end:
        if words[j].deprel == "cc":
            words[j].toLogical()
            if words[j].text == "[AND]":
                andCount += 1
            else:
                orCount += 1
            
            # Remove preceeding puncts
            if j-1 >= 0 and words[j-1].text == ",":
                words[j-1].text = ""
            #print("CC", words[j])
        #else:
        #    print(words[j].text)
        j += 1
    if andCount > 0 and orCount > 0:
        logger.warning('Found both "and" and "or" logical operators in component, '+
                        "please review manually to solve encapsulation issues.")

    return words

# Function that tries to use the old dependency parse tree for the second part of sentences starting
# with an activation condition. If the words do not include a root connection the words are
# parsed again.
def removeStart(words, offset, wordLen):
    i = 0

    noRoot = True
    while i < wordLen:
        if words[i].head != 0:
            words[i].head -= offset
        if words[i].deprel == "root":
            noRoot = False

        words[i].id -= offset
        i+=1

    if noRoot:
        logger.error("Unable to reuse the second part of the statement's dependency parse tree"+
                      " in removeStart")
        if not useREST:
            return compoundWordsMiddleware(nlpPipeline(WordsToSentence(words)))
        else:
            return compoundWordsMiddlewareWords(nlpPipeline(WordsToSentence(words)))

    return words

def corefReplace(words):
    #print("INITIALIZING COREF CHAIN FINDING:\n\n ")
    i = 0
    wordLen = len(words)
    
    brackets = 0
    while i < wordLen:
        if (words[i].symbol == "A" and words[i].pos == "PRON" and 
            words[i].coref != "" and words[i].position == 0):
            #print(words[i].text, i)
            words = addWord(words, i, words[i].text)
            i+=1
            wordLen += 1
            #print("word has coref", words[i].text, "Coref is: ", words[i].coref)
            corefLen = len(words[i].coref)
            #print(words[i].coref)
            if words[i].coref[corefLen-2:] == "'s":
                words[i].coref = words[i].coref[:corefLen-2]
            if words[i].coref[:4].lower() == "the ":
                words[i].coref = words[i].coref[4:]
            elif words[i].coref[:2] == "a ":
                words[i].coref = words[i].coref[2:]
            if ":poss" in words[i].deprel:
                words[i].coref += "'s"
            words[i].text = "["+words[i].coref+"]"
            words[i].spaces = 1
            logger.info("Replaced pronoun with coreference Attribute: "+ words[i-1].text+ ", "+
                              words[i].text)
            #print(words[i+1].text, i, "\n\n")
        elif words[i].pos == "PRON" and words[i].coref != "":
            if brackets == 0 and words[i].symbol == "":
                words = addWord(words, i, words[i].text)
                i+=1
                wordLen += 1
                corefLen = len(words[i].coref)
                print(words[i].coref)
                if words[i].coref[corefLen-2:] == "'s":
                    words[i].coref = words[i].coref[:corefLen-2]
                if words[i].coref[:4].lower() == "the ":
                    words[i].coref = words[i].coref[4:]
                elif words[i].coref[:2] == "a ":
                    words[i].coref = words[i].coref[2:]
                if ":poss" in words[i].deprel:
                    words[i].coref += "'s"
                words[i].text = "["+words[i].coref+"]"
                words[i].spaces = 1
                words[i].setSymbol("A")
                logger.info("Replaced pronoun with coreference Attribute: "+ words[i-1].text+ ", "+
                              words[i].text)
        else:
            if words[i].position == 1 and words[i].nested == False:
                brackets+=1
            if words[i].position == 2 and words[i].nested == False:
                brackets-=1
        i+=1
    
    return words

def compoundHandler(words, i):
    start = i
    end = words[i].head-1
    ccLocs = []
    ccType = ""
    punctLocs = []
    conjLocs = [i]

    if words[end].deprel == "obj":
        if start > end:
            logger.warning("compoundHandler: start > end")
            return start, False
        # Look for specific pattern:
        '''
        compound, (optional punct), cc, conj, compound
        or
        compound, (optional punct), conj, (optional punct), cc, conj, compound
        (repeated punct, conj n times before the compound)
        '''
        i+=1
        while i < end:
            #logger.debug("Word: " + words[i].text + " " + words[i].deprel)
            if words[i].deprel != "punct" and words[i].deprel != "cc" and words[i].deprel != "conj":
                logger.debug("compoundHandler: not punct cc or conj deprel")
                return start, False
            elif words[i].deprel == "cc":
                #logger.debug("Found cc: "+ words[i].text + " " + words[i].deprel)
                ccLocs.append(i)
                if ccType == "":
                    #logger.debug("Adding cc text")
                    ccType = words[i].text
                else:
                    if ccType != words[i].text:
                        logger.warning(
                    "compoundHandler: Detected several different types of logical operators.")
                        return start, False
            elif words[i].deprel == "punct":
                if words[i+1].deprel == "cc":
                    words[i].text = ""
                else:
                    punctLocs.append(i)
            else:
                conjLocs.append(i)
            i+=1

        if len(ccLocs) == 0 or ccType == "":
            logger.warning(
                    "compoundHandler did not detect a logical operator.")
            return start, False
        if len(conjLocs == 0):
            logger.warning(
                    "compoundHandler did not detect any conj dependencies.")
            return start, False
        else:
            for ccLoc in ccLocs:
                words[ccLoc].toLogical()
            for punct in punctLocs:
                words[punct].text = words[ccLocs[0]].text
                words[punct].spaces = 1
            conjLocs = conjLocs[:len(conjLocs)-1]
            for conj in conjLocs:
                logger.debug("Word in conjLocs: " + words[conj].text)
                words[conj].text = words[conj].text + " [" + words[end].text + "]"

        words[start].setSymbol("Bdir", 1)
        words[end].setSymbol("Bdir", 2)
        return end, True
    else:
        logger.debug("compoundHandler: Head is not an object")
        return start, False