import time
import copy
from matchingFunction import (
    conditionHandler, orElseHandler, bdirHandler, bindHandler,
    nmodDependencyHandler, executionConstraintHandler)
from utility import *
from matchingUtils import *
from matchingUtilsConstitutive import *

# Global variables for implementation specifics
CombineObjandSingleWordProperty = True
minimumCexLength = 1
semanticAnnotations = True
numberAnnotation = False
coref = True

def matchingHandlerConstitutive(words:list[Word]) -> list[Word]:
    """takes a list of words, performs annotations using the matching function and returns 
    a formatted string of annotated text"""
    words = compoundWordsHandler(words)
    words = matchingFunctionConstitutive(words)
    if coref: words = corefReplaceConstitutive(words, semanticAnnotations)
    if semanticAnnotations and numberAnnotation: words = attributeSemantic(words)
    return WordsToSentence(words)

def matchingFunctionConstitutive(words:list[Word]) -> list[Word]:
    """takes a list of words with dependency parse and pos-tag data.
       Returns a list of words with IG Script notation symbols."""
    wordLen = len(words)
    wordsBak = copy.deepcopy(words)
    i = 0
    words2 = []

    while i < wordLen:
        word = words[i]
        deprel = word.deprel

        #print(words[words[i].head], words[i].deprel, words[i].text)

        match deprel:
            # (Cac, Cex) Condition detection 
            case "advcl":
                if conditionHandler(words, wordsBak, i, wordLen, words2, True):
                    return words2
                
            # (Bdir) Object detection
            case "obj":
                i = bdirHandler(words, i, wordLen)

            # (Bind) Indirect object detection
            case "iobj":
                i = bindHandler(words, i, wordLen)

            # (I) Aim detection
            case "root":
                i = rootHandlerConstitutive(words, i, wordLen)

            # Else if the word has an amod dependency type, check if the head is a symbol
            # that supports properties, if so, the word is a property of that symbol
            # (Bdir,p, Bind,p, A,p)    
            case "amod":
                i = amodPropertyHandler(words, i, wordLen)
                # If the relation is a ccomp then handle it as a direct object
                # This does nothing in testing
                '''
                elif (words[word.head].deprel == "nsubj" 
                    and words[words[word.head].head].deprel == "ccomp"):
                    #print("\n\nAMOD NSUBJ OBJ\n\n")
                    word.setSymbol(word,"bdir", 1)
                    words[i+1].setSymbol(words[i+1],"bdir", 2)
                    i += 1
                '''
            case "acl":
                # (A,p) Attribute property detection 2
                if words[word.head].symbol == "E":
                    word.setSymbol("E,p")
                # (Bdir,p) Direct object property detection 3
                # TODO: Reconsider in the future if this is accurate enough
                # There are currently false positives, but they should be mitigated by better
                # Cex component detection
                if words[word.head].symbol == "Bdir" and words[i-1].symbol == "Bdir":
                    word.setSymbol("Bdir,p")

            # Direct object handling (Bdir), (Bdir,p)
            case "nmod":
                i = nmodDependencyHandler(words, i, wordLen)
                # TODO: Revisit and test
                #else if words[word.head].symbol == "A":
                #   print("\nnmod connected to Attribute(A): ", word)

            # (Bdir,p) Direct object property detection 2
            case "nmod:poss":
                if words[word.head].deprel == "obj" and word.head == i+1:
                    # Check if there is a previous amod connection and add both
                    if words[i-1].deprel == "amod" and words[i-1].head == i:
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
                    orElseHandler(words, wordsBak, wordLen, words2, i, True)
                    return words2
            # Advmod of Aim is correlated with execution constraints (Cex)
            # Might be too generic of a rule.
            # TODO: Revisit and test
            case "advmod":
                if words[word.head].symbol == "F":
                    #print("\nadvmod connected to Aim(I): ", word)
                    if i+1 < wordLen:
                        if words[i+1].deprel == "punct":
                            word.setSymbol("Cex")
            
            # (Cex) Execution constraint detection
            case "obl":
                i = executionConstraintHandler(words, i, wordLen, True)
            case "obl:tmod":
                # Old implementation used
                # i = words[i].head
                i = executionConstraintHandler(words, i, wordLen, True)

            # Default, for matches based on more than just a single deprel
            case _:
                # Print out more complex dependencies for future handling
                #if ":" in deprel:
                #    if deprel != "aux:pass" and deprel != "obl:tmod":
                #        print("\n", '":" dependency: ',words[i], "\n")
                
                # (A) Attribute detection
                # TODO: Consider specyfing which nsubj dependencies specifically to include
                if "nsubj" in deprel:
                    i = constitutedEntityHandler(words, i, wordLen)

                    # TODO: look into the line below
                    if words[word.head].deprel == "ccomp":
                        logger.debug("NSUBJ CCOMP OBJ")

                # (D) Deontic detection
                elif words[word.head].deprel == "root" and "aux" in deprel:
                    i = modalHandler(words, i)

                elif (deprel != "punct" and deprel != "conj" and deprel != "cc"
                      and deprel != "det" and deprel != "case"):
                    logger.debug("Unhandled dependency: " + deprel)
        
        # Iterate to the next word
        i += 1

    return words

def constitutedEntityHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for constituted entity (E) components detected using the nsubj dependency"""
    if words[i].pos != "PRON":
        # Look for nmod connected to the word i
        other = False
        for j in range(wordLen):
            if "nmod" in words[j].deprel and ifHeadRelation(words, j, i):
                #print("A with xpos: ", words[j], words[j].xpos)
                #print("Nmod head relation to a: ", words[j], words[i])
                j = smallLogicalOperator(words, j, "E", wordLen)
                other = True
                if words[i+1].deprel == "appos" and words[i+1].head == i:
                    if words[i].position == 2:
                        words[i].setSymbol("")
                        words[i+1].setSymbol("E",2)
                        i+=1
                    else:
                        words[i].setSymbol("E",1)
                        words[i+1].setSymbol("E",2)
                        i+=1
        if not other:
            i = smallLogicalOperator(words, i, "E", wordLen)
            if words[i+1].deprel == "appos" and words[i+1].head == i:
                if words[i].position == 2:
                    words[i].setSymbol("")
                    words[i+1].setSymbol("E",2)
                    i+=1
                else:
                    words[i].setSymbol("E",1)
                    words[i+1].setSymbol("E",2)
                    i+=1

    # If the nsubj is a pronoun connected to root then handle it as an attribute
    # This may need to be reverted in the future if coreference resolution is used
    # in that case, the coreference resolution will be used to add the appropriate attribute
    elif words[words[i].head].deprel == "root":
        i = smallLogicalOperator(words, i, "E", wordLen)
        if words[i+1].deprel == "appos" and words[i+1].head == i:
            if words[i].position == 2:
                words[i].setSymbol("")
                words[i+1].setSymbol("E",2)
                i+=1
            else:
                words[i].setSymbol("E",1)
                words[i+1].setSymbol("E",2)
                i+=1

    # (A,p) detection mechanism, might be too specific. 
    # Is overwritten by Aim (I) component in several cases
    if words[i+1].deprel == "advcl" and words[words[i+1].head].deprel == "root":
        #print("ADVCL")
        words[i+1].setSymbol("E,p")

    return i

def modalHandler(words:list[Word], i:int) -> int:
    """Handler for modal (M) components detected using the aux dependency"""
    if words[words[i].head].pos == "VERB":
        #print("Modal: ", words[i].xpos) 
        #Might be worth looking into deontics that do not have xpos of MD
        # Combine two adjacent deontics if present.
        if words[i-1].symbol == "M":
            words[i-1].setSymbol("M",1)
            words[i].setSymbol("M",2)
        else:
            if (words[i].head - i) > 1:
                words[i].setSymbol("M",1)
                i = words[i].head-1
                words[i].setSymbol("M",2)
            else:
                words[i].setSymbol("M")
    else:
        logger.debug("Modal, no verb")

    return i

def rootHandlerConstitutive(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for Constitutive Function (F) components detected using the root dependency"""
    # Potentially unmatch all occurences where the aim is not a verb
    #if words[i].pos != "VERB":
    #    print("Aim is not VERB:", words[i].pos, words[i])
    # Look for logical operators
    words[i].setSymbol("F")
    i = smallLogicalOperator(words, i, "F", wordLen)
    if words[i].position == 0:
        # Look for xcomp dependencies
        k = 0

        for k in range(wordLen):
            if words[k].deprel == "xcomp" and words[k].head == i:
                #print("XComp of I: ", words[k], k, i)
                # If the xcomp is adjacent encapsulate it in the aim component
                if k-i == 2:
                    words[i].setSymbol("F",1)
                    words[i+2].setSymbol("F",2)
                    i = k
                    break
                else:
                    j = i+1
                    while j < k-1:
                        if words[j].head != k:
                            # Add semantic annotation for context based on xcomp
                            # if the xcomp is not adjacent to the aim
                            words[i].text = (words[i].text + " " * words[k].spaces + "[" + 
                                                words[k].text + "]")
                            j = k
                            break
                        j+=1
                    if j == k-1:
                        # If the xcomp is adjacent encapsulate it in the aim component
                        words[i].setSymbol("F",1)
                        words[k].setSymbol("F",2)
                        i = k
    return i

def amodPropertyHandler(words:list[Word], i:int, wordLen:int) -> int:
    """Handler for properties detected using the amod dependency. Currently used for 
       Direct object (Bdir), Indirect object (Bind) and Attribute (A) properties (,p)"""
    # If the word is directly connected to an obj (Bdir)
    if words[words[i].head].deprel == "obj":
        i = smallLogicalOperator(words, i, "Bdir,p", wordLen)
        #words[i].setSymbol("Bdir,p")
    # Else if the word is directly connected to an iobj (Bind)
    elif words[words[i].head].deprel == "iobj":
        i = smallLogicalOperator(words, i, "Bind,p", wordLen)
        #words[i].setSymbol("Bind,p")
    # Else if the word is connected to a nsubj connected directly to root (Attribute)
    elif (words[words[i].head].deprel == "nsubj" 
            and (words[words[words[i].head].head].deprel == "root" or 
            words[words[words[i].head].head].symbol == "E")):
        i = smallLogicalOperator(words, i, "E,p", wordLen)
        #words[i].setSymbol("A,p")
    return i