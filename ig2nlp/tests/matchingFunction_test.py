from ig2nlp.matchingFunction import *
import pytest

def createTestWord(text:str) -> Word:
    word = Word(text,"","",0,0,"","","")
    return word

def createCC(text:str, id:int) -> Word:
    word = createTestWord(text)
    word.deprel = "cc"
    word.pos = "CCONJ"
    word.head = id+2
    word.spaces = 1
    return word

def createComma(id:int) -> Word:
    word = createTestWord(",")
    word.deprel = "punct"
    word.pos = "PUNCT"
    word.head = id+2
    return word

def createConj(text:str, headId:int) -> Word:
    word = createTestWord(text)
    word.head = headId+1
    word.deprel = "conj"
    word.pos = "NOUN"
    word.spaces = 1
    return word

def test_smallLogicalOperator():
    words:list[Word] = []
    words.append(createTestWord("a"))
    words[0].deprel = "root"
    words[0].symbol == ("I")
    words.append(createCC("and", 1))
    words.append(createConj("b", 0))

    # Assert that it works for the Aim (I) component on a basic case
    # "a and b"
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 2
    assert WordsToSentence(wordsBak) == "I(a [AND] b)"

    # Assert that it works for other components on a basic case
    wordsBak = copy.deepcopy(words)
    wordsBak[0].deprel = "Bdir"
    i = smallLogicalOperator(wordsBak, 0, "Bdir", len(words))
    assert i == 2
    assert WordsToSentence(wordsBak) == "Bdir(a [AND] b)"

    # Third item in logical operator chain
    # "a and b and c"
    words.append(createCC("and", 3))
    words.append(createConj("c",0))
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 4
    assert WordsToSentence(wordsBak) == "I(a [AND] b [AND] c)"

    # Both and and or
    # "a and b or c"
    words[3].text = "or"
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 4
    assert WordsToSentence(wordsBak) == "I(a [AND] (b [OR] c))"

    # and-or-and
    # "a and b or c and d"
    words.append(createCC("and",5))
    words.append(createConj("d",0))
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 6
    assert WordsToSentence(wordsBak) == "I(a [AND] (b [OR] c) [AND] d)"

    # or-and-or
    # "a or b and c or d"
    for word in words:
        if word.text == "and":
            word.text = "or"
        elif word.text == "or":
            word.text = "and"
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 6
    assert WordsToSentence(wordsBak) == "I(a [OR] (b [AND] c) [OR] d)"

    # Combination of character capitalizaion and multiple operators
    # or-and-or-aNd-anD
    words.append(createCC("anD", 7))
    words.append(createConj("e", 0))
    words.append(createCC("anD", 9))
    words.append(createConj("f", 0))
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 10
    assert WordsToSentence(wordsBak) == "I(a [OR] (b [AND] c) [OR] (d [AND] e [AND] f))"

    # With commas / puncts
    # "a , b and c , d or e anD f"
    words[1].text = ","
    words[1].deprel = "punct"
    words[5].text = ","
    words[5].deprel = "punct"
    words[7].text = "or"
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 10
    assert WordsToSentence(wordsBak) == "I(a [AND] b [AND] (c [OR] d [OR] e) [AND] f)"

    # with a det dependency inside
    # "a , b and c or the c"
    words = words[:5]
    words.append(createCC("or", 6))
    words.append(createCC("the", 6))
    words[6].deprel = "det"
    words.append(createConj("d",0))
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 7
    assert WordsToSentence(wordsBak) == "I(a [AND] b [AND] (c [OR] d))"

    # with a amod dependency inside
    # "a , b and c or amod d"
    words[6].deprel = "amod"
    words[6].text = "amod"
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "I", len(words))
    assert i == 7
    assert WordsToSentence(wordsBak) == "I(a [AND] b [AND] (c [OR] amod d))"

    # Test the same function through the rootHandler
    wordsBak = copy.deepcopy(words)
    i = rootHandler(wordsBak, 0, len(words))
    assert i == 7
    assert WordsToSentence(wordsBak) == "I(a [AND] b [AND] (c [OR] amod d))"

    # With Bdir instead
    words[0].deprel = "obj"
    wordsBak = copy.deepcopy(words)
    i = smallLogicalOperator(wordsBak, 0, "Bdir", len(words))
    assert i == 7
    assert WordsToSentence(wordsBak) == "Bdir(a [AND] b [AND] (c [OR] amod d))"

    # With bdirHandler
    words[0].deprel = "obj"
    wordsBak = copy.deepcopy(words)
    i = bdirHandler(wordsBak, 0, len(words))
    assert i == 7
    assert WordsToSentence(wordsBak) == "Bdir(a [AND] b [AND] (c [OR] amod d))"