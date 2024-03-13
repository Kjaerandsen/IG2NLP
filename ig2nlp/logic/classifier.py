from enum import Enum
from utility import *

class docType(Enum):
   REGULATIVE = 0
   CONSTITUTIVE = 1

# "must"?
regulativeDeontics = ["shall", "will", "need", "must"]
# "may"?
constitutiveModals = ["should", "could", "can"]

shared = ["shall", "may"]

def classifier(words:list[Word]) -> str:
   """ Basic classifier based on a dictionary of Deontics / Modals to classify statements as either
   regulative or constitutive """
   for word in words:
      if word.deprel == "aux" and words[word.head].deprel == "root":
         text = word.text.lower()
         print("Deontic / Modal: ", text)
         if text in regulativeDeontics:
            return "Regulative  "
         elif text in constitutiveModals:
            return "Constitutive"
         elif text in shared:
            return "None        "
   return "None        "

def coverage(words:list[Word]) -> float:
   """Gives a percentage of component coverage of a statement."""
   wordLen = len(words)
   count = 0
   inComponent = False
   componentType = ""
   nested = False
   for word in words:
      # If not within a component
      if not inComponent:
         if word.symbol != "":
            if word.position == 0:
               count += 1
            elif word.position == 1:
               count += 1
               inComponent = True
               componentType = word.symbol
               nested = word.nested
            else:
               count += 1
               logger.warning("Found invalid nesting of components in coverage")
         elif word.text == ".":
            count += 1
      # If within a component
      else:
         # If the current word is a component end, with the same component type and nesting
         # TODO: handle multiple levels of nesting
         if word.position == 2 and word.symbol == componentType and nested == word.nested:
            count += 1
            componentType = ""
            inComponent = False
         else:
            count += 1
   
   if count != 0 and wordLen != 0:
      return count/wordLen 
   else:
      logger.warning("Empty wordLen or count in coverage")
      return 0