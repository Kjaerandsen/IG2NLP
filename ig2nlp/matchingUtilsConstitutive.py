from utility import *

def validateNestedConstitutive(words:list[Word]) -> bool:
    """Sets a requirement of both an Aim (I) and an Attribute (A) detected for a component to
       be regarded as nested."""
    Aim = False
    Attribute = False

    for word in words:
        if word.symbol == "E":
            Attribute = True
            if Aim:
                return True
        if word.symbol == "F":
            Aim = True
            if Attribute:
                return True
    return False

def corefReplaceConstitutive(words:list[Word], semanticAnnotations:bool) -> list[Word]:
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
        if words[i].symbol == "E":
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
                logger.info("Replacing Constituted Entity (E) pronoun with "+ 
                            "coreference resolution data: " 
                            + words[id].text + " -> " + corefStrings[key])
                words = addWord(words, id, words[id].text)
                words[id+1].text = "["+corefStrings[key]+"]"
                words[id+1].spaces = 1
                words[id+1].setSymbol("E")
                if val > 1 and semanticAnnotations:
                    words[id+1].addSemantic("Entity="+corefStrings[key])
        if val > 1 and semanticAnnotations:
            #print("val over 1")
            for id in locations[key]:
                #print(id, "adding entity semanticannotation")
                words[id].addSemantic("Entity="+corefStrings[key])
    
    return words

def constitutedEntitySemantic(words:list[Word]) -> list[Word]:
    """Adds Number=x semantic annotation to constituted entity (E) components in a list of words"""
    for word in words:
        if word.symbol == "E":
            if "Number=Sing" in word.feats:
                word.addSemantic("Number=Sing")
            if "Number=Plur" in word.feats:
                word.addSemantic("Number=Plur")

    return words
