from utility import *

def smallLogicalOperator(words:list[Word], i:int, symbol:str, wordLen:int) -> int:
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

    if symbol == "I":
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
                elif words[words[j].head].deprel == "conj":
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
    word = words[wordId]
    
    while words[word.head].deprel != "root":
        if word.deprel == "root":
            return False
        if word.head == headId:
            return True
        # Go to the head of the current word and iterate
        word = words[word.head]
    return False

# List of allowed head connections for the function below
allowedAimHeads = ["conj","cc","det","amod","advmod"]

def ifHeadRelationAim(words:list[Word], wordId:int, headId:int) -> bool:
    """Check if the word is connected to the headId through a head connection, 
    specifically for Aim (I) components"""
    while words[words[wordId].head].deprel != "root":
        if words[wordId].head == headId:
            return True
        if not words[words[wordId].head].deprel in allowedAimHeads:
            return False
        wordId = words[wordId].head
    # Exception for the case where the headId is the root
    if words[headId].deprel == "root":
        return True
    return False

def corefReplace(words:list[Word], semanticAnnotations:bool) -> list[Word]:
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
        if words[i].coref[corefLen-2:] == "'s":
            words[i].text = words[:corefLen-2]
        if ":poss" in words[i].deprel:
            words[i].coref += "'s"
    '''

    #print(str(corefIds), str(corefStrings), str(locations))
        
    for key, val in corefIds.items():
        #print(key,val, wordLen)
        for id in locations[key]:
            if words[id].pos == "PRON":
                logger.info("Replacing Attribute (A) pronoun with coreference resolution data: " 
                            + words[id].text + " -> " + corefStrings[key])
                words = addWord(words, id, words[id].text)
                words[id+1].text = "["+corefStrings[key]+"]"
                words[id+1].spaces = 1
                words[id+1].setSymbol("A")
                if val > 1 and semanticAnnotations:
                    words[id+1].addSemantic("Entity="+corefStrings[key])
        if val > 1 and semanticAnnotations:
            #print("val over 1")
            for id in locations[key]:
                #print(id, "adding entity semanticannotation")
                words[id].addSemantic("Entity="+corefStrings[key])
    
    return words

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

def attributeSemantic(words:list[Word]) -> list[Word]:
    """Adds Number=x semantic annotation to attribute components in a list of words"""
    for word in words:
        if word.symbol == "A":
            if "Number=Sing" in word.feats:
                word.addSemantic("Number=Sing")
            if "Number=Plur" in word.feats:
                word.addSemantic("Number=Plur")

    return words