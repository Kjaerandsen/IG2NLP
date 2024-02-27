from matchingUtils import *
import copy
import pytest

def createTestWord(text:str) -> Word:
   word = Word(text,"","",0,0,"","","")
   return word

def createCC(text:str, id:int) -> Word:
   word = createTestWord(text)
   word.deprel = "cc"
   word.pos = "CCONJ"
   word.head = id+1
   word.spaces = 1
   return word

def createComma(id:int) -> Word:
   word = createTestWord(",")
   word.deprel = "punct"
   word.pos = "PUNCT"
   word.head = id+1
   return word

def createConj(text:str, headId:int) -> Word:
   word = createTestWord(text)
   word.head = headId
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

   # With Bdir instead
   words[0].deprel = "obj"
   wordsBak = copy.deepcopy(words)
   i = smallLogicalOperator(wordsBak, 0, "Bdir", len(words))
   assert i == 7
   assert WordsToSentence(wordsBak) == "Bdir(a [AND] b [AND] (c [OR] amod d))"

def test_validateNested():
   words:list[Word] = []
   words.append(createTestWord("1"))
   words.append(createTestWord("2"))

   # No symbols
   assert validateNested(words) == False

   # Only aim
   words[0].setSymbol("I")
   assert validateNested(words) == False

   # Only attribute
   words[0].setSymbol("A")
   assert validateNested(words) == False

   # Both aim and attribute
   words[1].setSymbol("I")
   assert validateNested(words) == True

def test_ifHeadRelation():
   """Test for ifHeadRelation and ifHeadRelationAim functions"""
   words:list[Word] = []
   words.append(createTestWord("1"))
   words.append(createTestWord("2"))

   words[0].head = 0
   words[1].head = 0

   # Check if Word 1 is connected to word 0
   assert ifHeadRelation(words, 1, 0)

   # Check if Word 1 is connected to word 0 for aim (root deprel)
   words[0].deprel = "root"
   assert ifHeadRelationAim(words, 1, 0)

   # Check if word 1 is connected to itself (False)
   assert ifHeadRelation(words, 1, 1) == False
   assert ifHeadRelationAim(words, 1, 1) == False

   # Check the detection through two extra chains
   words.append(createTestWord("3"))
   words.append(createTestWord("4"))
   words[2].head = 3
   words[3].head = 1
   # 2 is now connected through 3 to 1, which is connected to 0
   # Making the tested chain -> 2-3-1-0

   # If head relation should fail because the head has a root deprel
   assert not ifHeadRelation(words, 2, 0)

   # It should now succeed as the head does not have a root deprel
   words[0].deprel = ""
   assert ifHeadRelation(words, 2, 0)

   # It should now fail as the word has a root deprel
   words[2].deprel = "root"
   assert not ifHeadRelation(words, 2, 0)
   
   # It should now fail as a link in the chain has a root deprel
   words[2].deprel = ""
   words[3].deprel = "root"
   assert not ifHeadRelation(words, 2, 0)

   # Should now fail because link in the chain are not in the allowedAimHeads
   words[3].deprel = ""
   words[0].deprel = "root"

   assert not ifHeadRelationAim(words,2,0)

   # Set all words to have allowed deprels
   for word in words:
      word.deprel="conj"

   # Should now be True
   assert ifHeadRelationAim(words,2,0)