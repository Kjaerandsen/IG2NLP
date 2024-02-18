from stanza.utility import *

def createTestWord(name):
    word = Word(name,"","",0,0,"","","")

    return word

'''
    Word class tests
'''

def test_word_toLogical():
    word = createTestWord("and")

    word.toLogical()
    assert word.text == "[AND]"

def test_word_buildString():
    word = createTestWord("test")
    
    # Word without any spaces or symbols
    contents = word.buildString()
    assert contents == "test"

    # Word with 3 spaces
    word.spaces = 3
    contents = word.buildString()
    assert contents == "   test"

    # Word with 1 space
    word.spaces = 1
    contents = word.buildString()
    assert contents == " test"

    # Symbol position 0
    word.symbol = "A"
    contents = word.buildString()
    assert contents == " A(test)"

    # Symbol position 1
    word.position = 1
    contents = word.buildString()
    assert contents == " A(test"

    # Symbol position 2
    word.position = 2
    contents = word.buildString()
    assert contents == " test)"

    # Symbol nested position 2
    word.nested = True
    contents = word.buildString()
    assert contents == " test}"

    # Symbol nested position 21
    word.position = 1
    contents = word.buildString()
    assert contents == " A{test"

    # Symbol nested position 0
    word.position = 0
    contents = word.buildString()
    assert contents == " A{test}"

