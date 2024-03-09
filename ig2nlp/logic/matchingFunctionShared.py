from utility import *
import logic.matchingFunctionConstitutive as mc
import logic.matchingFunction as mr
from logic.classifier import *
import copy

numberAnnotation = False
coref = True

def parseAndCompare(words:list[Word], semantic:bool) -> tuple[list[Word],list[Word]]:

   words = compoundWordsHandler(words)
   words2 = copy.deepcopy(words)

   # Run the dictionary based classifier
   '''
   words3 = copy.deepcopy(words)
   classification = classifier(words3)
   '''

   words = mr.matchingFunction(words, semantic)
   #print(WordsToSentence(words))
   #print(WordsToSentence(words2))
   words2 = mc.matchingFunctionConstitutive(words2, semantic)
   

   if coref: words = mr.corefReplace(words, semantic)
   if semantic and numberAnnotation: words = mr.attributeSemantic(words)
   # Handle cases where a logical operator is included in a component without a matching word
   mr.logicalOperatorImbalanced(words)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   mr.handleScopingIssues(words)

   if coref: words2 = mc.corefReplaceConstitutive(words2, semantic)
   if semantic and numberAnnotation: words2 = mr.attributeSemantic(words2)
   # Handle cases where a logical operator is included in a component without a matching wor
   mr.logicalOperatorImbalanced(words2)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   mr.handleScopingIssues(words2)

   '''
   regulCov = coverage(words)
   constCov = coverage(words2)
   diff = regulCov-constCov
   if classification[:4] == "None":
      if diff > 0:
         return "Regulative   | Difference: Regulative   | Classifier: " + classification
      elif diff < 0:
         return "Constitutive | Difference: Constitutive | Classifier: " + classification
      else: 
         return "Regulative   | Difference: None         | Classifier: None"
   else:
      if diff > 0:
         return classification + " | Difference: Regulative   | Classifier: " + classification
      elif diff < 0:
         return classification + " | Difference: Constitutive | Classifier: " + classification
      else: 
         return classification + " | Difference: None         | Classifier: " + classification
   '''

   return WordsToSentence(words), WordsToSentence(words2)