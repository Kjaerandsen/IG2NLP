from utility import *
from logic.matchingFunction import *
from logic.classifier import *
import copy

numberAnnotation = False
coref = True

def parseAndCompare(words:list[Word], semantic:bool, 
                    constitutive:bool) -> tuple[list[Word],list[Word]]:

   words = compoundWordsHandler(words)
   words2 = copy.deepcopy(words)

   # Run the dictionary based classifier
   '''
   words3 = copy.deepcopy(words)
   classification = classifier(words3)
   '''

   words = matchingFunction(words, semantic, constitutive)
   #print(WordsToSentence(words))
   #print(WordsToSentence(words2))
   words2 = matchingFunction(words2, semantic, constitutive)
   

   if coref: words = corefReplace(words, semantic, constitutive)
   if semantic and numberAnnotation: words = entitySemantic(words, constitutive)
   # Handle cases where a logical operator is included in a component without a matching word
   logicalOperatorImbalanced(words)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   handleScopingIssues(words)

   if coref: words2 = corefReplace(words2, semantic, constitutive)
   if semantic and numberAnnotation: words2 = entitySemantic(words2, constitutive)
   # Handle cases where a logical operator is included in a component without a matching wor
   logicalOperatorImbalanced(words2)
   # Handle scoping issues (unclosed parentheses, or nesting in not nested components)
   handleScopingIssues(words2)

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