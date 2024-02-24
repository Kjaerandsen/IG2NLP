import time
import copy
from utility import *
from matchingUtils import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1
semanticAnnotations = False

def matchingHandler(words:list[Word]) -> list[Word]:
    """takes a list of words, performs annotations using the matching function and returns 
    a formatted string of annotated text"""
    return WordsToSentence(
            corefReplace(
                matchingFunction(
                    compoundWordsHandler(words)), semanticAnnotations))

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
    i = smallLogicalOperator(words, i, "I", wordLen)
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