import stanza
import time
import copy
import requests
from utility import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1
semanticAnnotations = True

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
            output = WordsToSentence(
            corefReplace(
                matchingFunction(
                    compoundWordsMiddleware(
                        words))))
        else:
            words = doc
            output = WordsToSentence(
            corefReplace(
                matchingFunction(
                    compoundWordsMiddlewareWords(
                        words))))
        
        #print(jsonData[i]['baseTx'] + "\n" + jsonData[i]['manual'] + "\n" + output)
        logger.debug("Statement"+ str(i) + ": " + jsonData[i]['name'] + " finished processing.")
        jsonData[i]["stanza"] = output
        i+=1

    logger.info("Finished running matcher\n\n")
    return jsonData

# Unused currently, used in orElseHandler and handleCondition if reverting to the earlier handling
# of the components
'''
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
'''
        
def nlpPipelineMulti(textDocs:list) -> list:
    """Takes a list of sentences as strings, returns the nlp pipeline results for the sentences"""
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

def matchingFunction(words:list[Word]) -> list[Word]:
    """takes a list of words with dependency parse and pos-tag data.
       Returns a list of words with IG Script notation symbols."""
    wordLen = len(words)
    wordsBak = copy.deepcopy(words)
    i = 0
    words2 = []

    while i < wordLen:
        word = words[i]
        deprel = word.deprel

        #print(words[words[i].head-1], words[i].deprel, words[i].text)

        match deprel:
            # (Cac, Cex) Condition detection 
            case "advcl":
                if conditionHandler(words, wordsBak, i, wordLen, words2):
                    return words2
                
            # (Bdir) Object detection
            case "obj":
                i = bdirHandler(words, i, wordLen)

            # (Bind) Indirect object detection
            case "iobj":
                i = bindHandler(words, i, wordLen)

            # (I) Aim detection
            case "root":
                i = rootHandler(words, i, wordLen)

            # Else if the word has an amod dependency type, check if the head is a symbol
            # that supports properties, if so, the word is a property of that symbol
            # (Bdir,p, Bind,p, A,p)    
            case "amod":
                i = amodPropertyHandler(words, i, wordLen)
                # If the relation is a ccomp then handle it as a direct object
                # This does nothing in testing
                '''
                elif (words[word.head-1].deprel == "nsubj" 
                    and words[words[word.head-1].head-1].deprel == "ccomp"):
                    #print("\n\nAMOD NSUBJ OBJ\n\n")
                    word.setSymbol(word,"bdir", 1)
                    words[i+1].setSymbol(words[i+1],"bdir", 2)
                    i += 1
                '''
            case "acl":
                # (A,p) Attribute property detection 2
                if words[word.head-1].symbol == "A":
                    word.setSymbol("A,p")
                # (Bdir,p) Direct object property detection 3
                # TODO: Reconsider in the future if this is accurate enough
                # There are currently false positives, but they should be mitigated by better
                # Cex component detection
                if words[word.head-1].symbol == "Bdir" and words[i-1].symbol == "Bdir":
                    word.setSymbol("Bdir,p")

            # Direct object handling (Bdir), (Bdir,p)
            case "nmod":
                i = nmodDependencyHandler(words, i, wordLen)
                # TODO: Revisit and test
                #else if words[word.head-1].symbol == "A":
                #   print("\nnmod connected to Attribute(A): ", word)

            # (Bdir,p) Direct object property detection 2
            case "nmod:poss":
                if words[word.head-1].deprel == "obj" and word.head-1 == i+1:
                    # Check if there is a previous amod connection and add both
                    if words[i-1].deprel == "amod" and words[i-1].head-1 == i:
                        words[i-1].setSymbol("Bdir,p", 1)
                        word.setSymbol("Bdir,p", 2)
                    # Else only add the Bdir,p
                    else:
                        word.setSymbol("Bdir,p")
                #else:
                    #print("\nWord is nmod:poss: ", word)
            
            # (O) Or else detection
            case "cc":
                if words[i+1].text == "else":
                    orElseHandler(words, wordsBak, wordLen, words2, i)
                    return words2
            # Advmod of Aim is correlated with execution constraints (Cex)
            # Might be too generic of a rule.
            # TODO: Revisit and test
            case "advmod":
                if words[word.head-1].symbol == "I":
                    #print("\nadvmod connected to Aim(I): ", word)
                    if i+1 < wordLen:
                        if words[i+1].deprel == "punct":
                            word.setSymbol("Cex")
            
            # (Cex) Execution constraint detection
            case "obl":
                i = executionConstraintHandler(words, i, wordLen)
            case "obl:tmod":
                # Old implementation used
                # i = words[i].head-1
                i = executionConstraintHandler(words, i, wordLen)

            # Default, for matches based on more than just a single deprel
            case _:
                # Print out more complex dependencies for future handling
                #if ":" in deprel:
                #    if deprel != "aux:pass" and deprel != "obl:tmod":
                #        print("\n", '":" dependency: ',words[i], "\n")
                
                # (A) Attribute detection
                # TODO: Consider specyfing which nsubj dependencies specifically to include
                if "nsubj" in deprel:
                    i = attributeHandler(words, i, wordLen)

                    # TODO: look into the line below
                    if words[word.head-1].deprel == "ccomp":
                        logger.debug("NSUBJ CCOMP OBJ")

                # (D) Deontic detection
                elif words[word.head-1].deprel == "root" and "aux" in deprel:
                    i = deonticHandler(words, i)

                elif (deprel != "punct" and deprel != "conj" and deprel != "cc"
                      and deprel != "det" and deprel != "case"):
                    logger.debug("Unhandled dependency: " + deprel)
        
        # Iterate to the next word
        i += 1

    return words

def validateNested(words:list[Word]) -> bool:
    """Sets a requirement of both an Aim (I) and an Attribute (A) detected for a component to
       be regarded as nested."""
    Aim = False
    Attribute = False

    for word in words:
        if word.symbol == "A":
            Attribute = True
            if Aim:
                return True
        if word.symbol == "I":
            Aim = True
            if Attribute:
                return True
    return False

def ifHeadRelation(words:list[Word], wordId:int, headId:int) -> bool:
    """Check if the word is connected to the headId through a head connection"""
    while words[words[wordId].head-1].deprel != "root":
        if words[wordId].deprel == "root":
            return False
        if words[wordId].head-1 == headId:
            return True
        wordId = words[wordId].head-1
    return False

# List of allowed head connections for the function below
allowedAimHeads = ["conj","cc","det","amod","advmod"]

def ifHeadRelationAim(words, wordId, headId) -> bool:
    """Check if the word is connected to the headId through a head connection, 
    specifically for Aim (I) components"""
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

def smallLogicalOperator(words:list[Word], i:int, symbol:str, wordLen:int, aim=False) -> int:
    """Finds the scope of components with logical operators and handles the logical operators"""
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
        for j in range(scopeStart, scopeEnd):
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

        # Remove dets
        for det in detLocs:
            k = det
            words[k].spaces = 0
            words[k].text = ""

        words[scopeStart].setSymbol(symbol, 1)
        words[scopeEnd].setSymbol(symbol, 2)
        
        i = scopeEnd

        # If there is only one CC in the component
        if ccCount == 1:
            # Set the contents of the cc to be a logical operator
            words[ccLocs[0]].toLogical()

            # Turn all extra punct deprels into the same logical operator as above
            for punct in punctLocs:
                words[punct].spaces += 1
                words[punct].text = words[ccLocs[0]].text

        else:
            # Go through the list of words, create lists of logical operator sequences
            ccLocs2 = []
            ccTypes = []
            orConj = False
            andConj = False

            ccLocs = ccLocs + punctLocs

            for j in range(scopeStart, scopeEnd+1):
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
            
            originalType = ccTypes[0]
            prevOperator = ccTypes[0]
            prevOperatorLoc = ccLocs2[0]
            # If there is a mix and match between symbol types handle the bracketing
            if andConj and orConj:
                logger.warning('Found both "and" and "or" logical operators in component, '+
                        "please review manually to solve potential encapsulation issues.")

                # Go through all the cc and handle the bracketing
                for nextLoc, nextType in zip(ccLocs2, ccTypes):
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

            # If the last operator is not the original add a closing bracket
            if ccTypes[len(ccLocs2)-1] != originalType:
                words[scopeEnd].text += ")"
            
            logger.warning("More than one CC in smallLogicalOperator function, " +
                             "please review logical operators")
            
        return scopeEnd
    
    else:
        words[i].setSymbol(symbol)
        return i

def LogicalOperatorHelper(word:list[Word], wordLen:int, scopeEnd:int, 
                          ccLocs:list[int], j:int) -> tuple[int, int]:
    """Adds cc deprels to ccLocs and escapes the sequence if
       an unsupported deprel is detected"""
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

def conditionHandler(words:list[Word], wordsBak:list[Word], i:int, 
                     wordLen:int, words2:list[Word]) -> bool:
    """Handler function for the matching and encapsulation of conditions (Cac, Cex)"""
    firstVal = i
    
    # Go through the statement until the word is connected to the advcl directly or indirectly
    for j in range(i):
        # If connected to the advcl then set firstVal to the id and break the loop
        if ifHeadRelation(words, j, i):
            firstVal = j
            break

    # Go through again from the activation condition++
    # Until the word is no longer connected to the advcl
        
    # Set the lastVal to the current id -1    
    lastIndex = i+1
    for j in range(i+1,wordLen):
        if not ifHeadRelation(words, j, i):
            lastIndex = j-1
            break

    if words[lastIndex].deprel != "punct":
        if words[lastIndex+1].deprel == "punct":
            lastIndex += 1
        else:
            logger.debug("Last val in handleCondition was not punct: " + words[lastIndex].text)
            return False

    date = False
    if firstVal == 0:
        contents = []

        '''
        condition = matchingFunction(
            compoundWordsMiddlewareWords(nlpPipeline(WordsToSentence(wordsBak[:lastIndex]))))
        '''
        #TODO: Test this further, the configuration above had a different outcome in one case
        condition = matchingFunction(reusePartSoS(wordsBak[:lastIndex], lastIndex))

        oblCount = 0
        for conditionWord in condition:
            if "obl" in conditionWord.deprel:
                oblCount+=1
            if "DATE" in conditionWord.ner:
                date = True

        if oblCount > 1 and words[0].deprel == "mark":
            symbol = "Cex"
        else:
            symbol = "Cac"
            date = False

        '''
        if date:
            logger.debug("Date in condition: " + symbol + WordsToSentence(condition))
        elif symbol == "Cex":
            logger.debug("No Date in Execution Constraint: " + symbol + WordsToSentence(condition))
        '''

        if validateNested(condition):
            words2.append(Word(
            "","","",0,0,"","","",0,0,0,symbol,True,1
            ))
            if date and semanticAnnotations:
                words2[len(words2)-1].semanticAnnotation = "ctx:tmp"
            condition[0].spaces = 0
            words2 += condition
            words2.append(Word("","","",0,0,"","","",0,0,0,symbol,True,2))
            words2.append(words[lastIndex])
        else:
            words2 += words[:lastIndex]
            words2[0].setSymbol(symbol,1)
            if date and semanticAnnotations:
                words2[0].semanticAnnotation = "ctx:tmp"
            words2[lastIndex-1].setSymbol(symbol,2)
            words2.append(words[lastIndex])
            if lastIndex - firstVal > 2:
                words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)

        #contents = matchingFunction(compoundWordsMiddleware(nlpPipeline(
        #    WordsToSentence(words[lastIndex+1:]))))
        contents = matchingFunction(reusePartEoS(words[lastIndex+1:], lastIndex+1))

        # Copy over the old placement information to the 
        # newly generated words for proper formatting
        for j in range(lastIndex+1, wordLen):
            index = j-lastIndex-1
            contents[index].id = words[j].id
            contents[index].start = words[j].start
            contents[index].end = words[j].end
            contents[index].spaces = words[j].spaces

        # print("Contents are: '", contents[0].text, "'")
        words2 += contents

        return True
    elif words[firstVal].deprel == "mark":
        #print("First val was not id 0 and deprel was mark", words[lastIndex])
        # Do the same as above, but also with the words before this advcl
        contents = []

        # Add the values before the condition
        words2 += words[:firstVal]
        condition = matchingFunction(
                reusePartMoS(copy.deepcopy(wordsBak[firstVal:lastIndex]), firstVal, lastIndex))

        j = 0
        oblCount = 0
        for conditionWord in condition:
            if "obl" in conditionWord.deprel:
                oblCount+=1
            if "DATE" in conditionWord.ner:
                date = True

        if oblCount > 1:
            symbol = "Cex"
        else:
            symbol = "Cac"
            date = False

        if validateNested(condition):
            words2.append(Word(
            "","","",0,0,"","","",0,0,1,symbol,True,1
            ))
            if date and semanticAnnotations:
                words2[len(words2)-1].semanticAnnotation = "ctx:tmp"
            condition[0].spaces = 0
            words2 += condition
            words2.append(Word("","","",0,0,"","","",0,0,0,symbol,True,2))
            words2.append(words[lastIndex])
        else:
            words2 += wordsBak[firstVal:lastIndex]
            words2[firstVal].setSymbol(symbol,1)
            if date and semanticAnnotations:
                words2[firstVal].semanticAnnotation = "ctx:tmp"
            words2[lastIndex-1].setSymbol(symbol,2)
            words2.append(words[lastIndex])
            if lastIndex - firstVal > 2:
                words2 = findInternalLogicalOperators(words2, firstVal, lastIndex)
        
        if wordLen > lastIndex+1:
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
            for j in range(lastIndex+1, wordLen):
                index = j-lastIndex-1
                contents[index].id = words[j].id
                contents[index].start = words[j].start
                contents[index].end = words[j].end
                contents[index].spaces = words[j].spaces

            # print("Contents are: '", contents[0].text, "'")
            words2 += contents
            if lastPunct:
                words2.append(wordsBak[lastVal])

        return True
    else:
        #print("First val was not id 0 and deprel was not mark", words[lastIndex])
        return False

def orElseHandler(words:list[Word], wordsBak:list[Word], wordLen:int,
                  words2:list[Word], firstVal:int):
    """Handler function for the Or else (O) component"""

    # Include everything but the last punct if it exists    
    if words[wordLen-1].deprel == "punct":
        lastIndex = wordLen -1
    else:
        lastIndex = wordLen

    # Add the values before the condition
    words2 += words[:firstVal]

    orElseComponent = matchingFunction(
            reusePartEoS(wordsBak[firstVal+2:lastIndex], firstVal+2))
    orElseComponent[0].spaces = 0

    words2.append(Word(
    "","","",0,0,"","","",0,0,1,"O",True,1
    ))
    words2 += orElseComponent
    words2.append(Word("","","",0,0,"","","",0,0,0,"O",True,2))
    # Append the last punct
    if words[wordLen-1].deprel == "punct":
        words2.append(words[wordLen-1])

def executionConstraintHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for execution constraint (Cex) components detected using the obl dependency"""
    # Check for connections to the obl both before and after
    scopeStart = i
    scopeEnd = i

    for j in range(wordLen):
        if (ifHeadRelation(words, j, i) 
                and words[j].deprel != "punct"):
            if j > scopeEnd:
                scopeEnd = j
            elif j < scopeStart:
                scopeStart = j
    
    if scopeEnd - scopeStart >= minimumCexLength:
        #TODO: Reconsider the two lines below in the future
        # (removal of case, det in the component start, i.e. "of the")
        #if words[scopeStart].deprel == "case" and words[scopeStart+1].deprel == "det":
        #    scopeStart += 2
        
        
        # Check for Date NER in the component
        componentWords = words[scopeStart:scopeEnd+1]

        date = False
        for word in componentWords:
            if "DATE" in word.ner:
                date = True
        #if not date:
        #    return i
        
        '''
        if date:
            logger.debug("Date in Execution Constraint (obl): " + 
                            WordsToSentence(componentWords) + " " +
                            str(len(componentWords)))
        else:
            logger.debug("No date in Execution Constraint (obl): " + 
                            WordsToSentence(componentWords) + " " +
                            str(len(componentWords)))
        '''

        # Add the words as a Cex
        #print("Setting CEX", WordsToSentence(words[scopeStart:scopeEnd+1]))
        words[scopeStart].setSymbol("Cex", 1)
        if date and semanticAnnotations:
            words[scopeStart].semanticAnnotation = "ctx:tmp"
        words[scopeEnd].setSymbol("Cex", 2)
        if scopeEnd - scopeStart > 2:
            words = findInternalLogicalOperators(words, scopeStart, scopeEnd)
    
    return scopeEnd


def findInternalLogicalOperators(words:list[Word], start:int, end:int) -> list[Word]:
    """Detects logical operator words, formats them, and replaces preceeding commas with the same
       logical operator"""
    #print("Finding logical operators\n", start, end)
    andCount = 0
    orCount = 0
    for j in range(start, end):
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
    if andCount > 0 and orCount > 0:
        logger.warning('Found both "and" and "or" logical operators in component, '+
                        "please review manually to solve encapsulation issues.")

    return words

def corefReplace(words:list[Word]) -> list[Word]:
    """Handles supplementing pronouns with their respective Attribute (A) component contents using
       coreference resolution data"""
    #print("INITIALIZING COREF CHAIN FINDING:\n\n ")
    i = 0
    wordLen = len(words)
    
    corefIds = {}
    locations = {}
    corefStrings = {}

    brackets = 0

    # Get all instances of a coref with the given id
    # if the length of the word is longer than another instance replace the coref string for that
    # coref with the new word
    while i < wordLen:
        if words[i].symbol == "A":
            if words[i].position != 2 and words[i].corefid != -1:
                if words[i].corefid in corefIds:
                    corefIds[words[i].corefid] += 1
                    locations[words[i].corefid].append(i)
                else:
                    corefIds[words[i].corefid] = 1
                    locations[words[i].corefid] = [i]

                if words[i].position == 0:
                    if words[i].corefid in corefStrings:
                        if len(corefStrings[words[i].corefid]) < len(words[i].text):
                            corefStrings[words[i].corefid]=words[i].text
                    else:
                        corefStrings[words[i].corefid]=words[i].text
                else:
                    iBak = i
                    while words[i].position != 2:
                        i+=1
                    if words[i].corefid in corefStrings:
                        if (len(corefStrings[words[i].corefid]) < 
                            len(WordsToSentence(words[iBak:i+1]))):
                            corefStrings[words[i].corefid]=WordsToSentence(words[iBak:i+1])
                    else:
                        corefStrings[words[i].corefid]=WordsToSentence(words[iBak:i+1])
        elif (words[i].symbol == "" and words[i].corefid != -1 
              and words[i].pos == "PRON" and brackets == 0):
            if words[i].corefid in corefIds:
                corefIds[words[i].corefid] += 1
                locations[words[i].corefid].append(i)
            else:
                corefIds[words[i].corefid] = 1
                locations[words[i].corefid] = [i]
        else:
            if words[i].position == 1 and words[i].nested == False:
                brackets+=1
            if words[i].position == 2 and words[i].nested == False:
                brackets-=1
        i += 1

    '''
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
        elif (words[i].pos == "PRON" and words[i].coref != "" and
              brackets == 0 and words[i].symbol == ""):
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
    '''

    #print(str(corefIds), str(corefStrings), str(locations))
        
    for key, val in corefIds.items():
        print(key,val, wordLen)
        for id in locations[key]:
            if words[id].pos == "PRON":
                print("ADDING PRON REPLACEMENT COREF")
                words = addWord(words, id, words[id].text)
                words[id+1].text = "["+corefStrings[key]+"]"
                words[id+1].spaces = 1
                words[id+1].setSymbol("A")
                if val > 1 and semanticAnnotations:
                    words[id+1].semanticAnnotation = "Entity="+corefStrings[key]
        if val > 1 and semanticAnnotations:
            #print("val over 1")
            for id in locations[key]:
                print(id, "adding entity semanticannotation")
                words[id].semanticAnnotation = "Entity="+corefStrings[key]
    
    return words

def attributeHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for attribute (A) components detected using the nsubj dependency"""
    if words[i].pos != "PRON":
        # Look for nmod connected to the word i
        other = False
        for j in range(wordLen):
            if "nmod" in words[j].deprel and ifHeadRelation(words, j, i):
                #print("A with xpos: ", words[j], words[j].xpos)
                #print("Nmod head relation to a: ", words[j], words[i])
                j = smallLogicalOperator(words, j, "A", wordLen)
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
        if not other:
            i = smallLogicalOperator(words, i, "A", wordLen)
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
        i = smallLogicalOperator(words, i, "A", wordLen)
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

    return i

def deonticHandler(words:list[Word], i:int) -> int:
    """Handler for deontic (D) components detected using the aux dependency"""
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
                i = words[i].head-2
                words[i].setSymbol("D",2)
            else:
                words[i].setSymbol("D")
    else:
        logger.debug("Deontic, no verb")

    return i

def rootHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for Aim (I) components detected using the root dependency"""
    # Potentially unmatch all occurences where the aim is not a verb
    #if words[i].pos != "VERB":
    #    print("Aim is not VERB:", words[i].pos, words[i])
    # Look for logical operators
    words[i].setSymbol("I")
    i = smallLogicalOperator(words, i, "I", wordLen, True)
    if words[i].position == 0:
        # Look for xcomp dependencies
        k = 0

        for k in range(wordLen):
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
    return i

def bindHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for indirect object (Bind) components detected using the iobj dependency"""
    iBak = i
    i = smallLogicalOperator(words, i, "Bind", wordLen)

    # If the flag is True combine the object with single word properties preceeding 
    if CombineObjandSingleWordProperty:
        if (words[iBak-1].symbol == "Bind,p" and words[iBak-1].deprel == "amod"
            and words[iBak-1].position == 0):
            if iBak != i:
                words[iBak].setSymbol("", 0)
                words[iBak-1].setSymbol("Bind", 1)
            else:
                words[iBak].setSymbol("Bind", 2)
                words[iBak-1].setSymbol("Bind", 1)

    return i

def bdirHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for indirect object (Bdir) components detected using the iobj dependency"""
    iBak = i
    i = smallLogicalOperator(words, i, "Bdir", wordLen)
    # Positive lookahead for nmod to include:
    # May need future refinement
    # TODO: Look into positive lookahead vs, handling nmod separately as currently done
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

    return i

def amodPropertyHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for properties detected using the amod dependency. Currently used for 
       Direct object (Bdir), Indirect object (Bind) and Attribute (A) properties (,p)"""
    # If the word is directly connected to an obj (Bdir)
    if words[words[i].head-1].deprel == "obj":
        i = smallLogicalOperator(words, i, "Bdir,p", wordLen)
        #words[i].setSymbol("Bdir,p")
    # Else if the word is directly connected to an iobj (Bind)
    elif words[words[i].head-1].deprel == "iobj":
        i = smallLogicalOperator(words, i, "Bind,p", wordLen)
        #words[i].setSymbol("Bind,p")
    # Else if the word is connected to a nsubj connected directly to root (Attribute)
    elif (words[words[i].head-1].deprel == "nsubj" 
            and (words[words[words[i].head-1].head-1].deprel == "root" or 
            words[words[words[i].head-1].head-1].symbol == "A")):
        i = smallLogicalOperator(words, i, "A,p", wordLen)
        #words[i].setSymbol("A,p")
    return i

def nmodDependencyHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for nmod dependency, currently used for Direct object (Bdir) components 
    and its properties"""
    # Too broad coverage in this case, detected instances which should be included in the main
    # object in some instances, an instance of an indirect object component, and several 
    # overlaps with execution constraints.
    # TODO: Look into nmod inclusion further
    if words[words[i].head-1].symbol == "Bdir" and words[words[i].head-1].position in [0,2]:
        #logger.debug("NMOD connected to BDIR")
        # positive lookahead
        firstIndex = i
        doubleNmod = False
        # Find and encapsulate any other nmods connected to the last detected nmod
        for j in range(wordLen):
            if words[j].deprel == "nmod" and words[j].head-1 == i:
                lastIndex = j
                doubleNmod = True
                i = j
        
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
    return i