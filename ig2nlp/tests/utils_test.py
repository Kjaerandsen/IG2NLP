from utility import *
import pytest

def createTestWord(name):
    word = Word(name,"","",0,0,"","","")

    return word

'''
    Word class tests
'''

def test_Word_combineWords():
    # Test function without spaces
    # Left to Right
    word1 = createTestWord("1")
    word2 = createTestWord("2")
    word1.combineWords(word2, False)
    assert word1.text == "21"
    # Right to Left
    word1 = createTestWord("1")
    word1.combineWords(word2, True)
    assert word1.text == "12"


    # Test function with spaces
    # Left to Right
    word1.text="1"
    word1.spaces = 1
    word1.combineWords(word2, False)
    assert word1.text == "2 1"

    # Right to Left
    word1.text="1"
    word2.spaces=2
    word1.combineWords(word2, True)
    assert word1.text == "1  2"

def test_Word_toLogical():
    word = createTestWord("and")

    word.toLogical()
    assert word.text == "[AND]"

def test_Word_setSymbol():
    word = createTestWord("and")

    word.setSymbol("A")
    assert word.position == 0 and word.symbol == "A" and word.nested == False

    word.setSymbol("B", 1)
    assert word.position == 1 and word.symbol == "B" and word.nested == False

    word.setSymbol("C", 2)
    assert word.position == 2 and word.symbol == "C" and word.nested == False

    word.setSymbol("A", 0, True)
    assert word.position == 0 and word.symbol == "A" and word.nested == True

    word.setSymbol("B", 1, True)
    assert word.position == 1 and word.symbol == "B" and word.nested == True

    word.setSymbol("C", 2, True)
    assert word.position == 2 and word.symbol == "C" and word.nested == True
    
    word.setSymbol("D")
    assert word.position == 0 and word.symbol == "D" and word.nested == False


def test_Word_buildString():
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

'''
    Tests for functions manipulating lists of Word class objects
'''

def test_addToCustomWords():
    words = []
    words.append(createTestWord("1"))

    addToCustomWords(words, createTestWord("2"), "ReplacedContents", 5, 10, 3)

    assert (len(words) == 2 and words[1].text == "ReplacedContents" and words[1].start == 5
            and words[1].end == 10 and words[1].spaces == 3)

# Test for removeWord function, tests that text contents are maintained, and error handling
# Does not test the head connection adjustment functionality
def test_removeWord():
    # Create wordist with text 0,1,2,3,4
    words = []
    i = 0
    while i < 5:
        words.append(createTestWord(str(i)))
        words[i].spaces = 1
        i+=1

    assert WordsToSentence(words) == " 0 1 2 3 4"

    # Remove the two(2), direction 0
    wordLen = len(words)
    i, wordLen = removeWord(words, 2, wordLen)
    assert len(words) == wordLen
    assert words[i+1].text == "2 3"

    assert WordsToSentence(words) == " 0 1 2 3 4"

    # Test for incorrect direction of removal (removing last word and combining with next word, or 
    # first and previous)
    with pytest.raises(Exception):
        _, _ = removeWord(words, 3, wordLen)
        
    with pytest.raises(Exception):
        _, _ = removeWord(words, 0, wordLen, 1)

    # Remove the one(1), direction 1
    i, wordLen = removeWord(words, 2, wordLen, 1)

    assert words[i].text == "1 2 3"

    assert WordsToSentence(words) == " 0 1 2 3 4"

    # Remove first and last elements
    i, wordLen = removeWord(words, 1, wordLen, 1)
    i, wordLen = removeWord(words, 0, wordLen, 0)

    # Now the only element left should contain all the contents
    assert words[i].text == "0 1 2 3 4"
    assert WordsToSentence(words) == " 0 1 2 3 4"

# Basic test of addWord function
# Does not test the head connection adjustment functionality
def test_addWord():
    words = []
    i = 0
    while i < 5:
        words.append(createTestWord(str(i)))
        words[i].spaces = 1
        i+=1

    # Add a word to the sentence
    words = addWord(words, 4, "3.5")

    assert words[4].text == "3.5"

def test_WordsToSentence():
    words:list[Word] = []
    i = 0
    while i < 5:
        words.append(createTestWord(str(i)))
        words[i].spaces = 1
        i+=1

    # Assert that the base sentence maintains formatting
    assert WordsToSentence(words) == " 0 1 2 3 4"

    # Add some components
    words[0].setSymbol("Cac", 0, True)
    words[1].setSymbol("A", 1)
    words[2].setSymbol("A", 2)

    # Add a word to the sentence
    words = addWord(words, 4, "3.5")

    # Verify the updated output
    assert WordsToSentence(words) == " Cac{0} A(1 2) 3 3.5 4"

def test_semanticAnnotation():
    # A new word should not have a semantic annotation present
    word=createTestWord("Word")
    assert word.buildString() == "Word"
    word.setSymbol("A")
    assert word.buildString() == "A(Word)"
    
    # Adding a semantic annotation should add it to the output
    word.semanticAnnotation = "X"
    assert word.buildString() == "A[X](Word)"

    # Resetting the semantic annotation to an empty string should remove it from the output
    word.semanticAnnotation = ""
    assert word.buildString() == "A(Word)"