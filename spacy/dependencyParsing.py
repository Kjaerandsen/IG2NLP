import spacy
from spacy import displacy
import sys

# Load the pretrained model
nlp = spacy.load("en_core_web_sm")
args = sys.argv

if len(args)<2:
    print('Error: a string must be passed with the function in the format:\ndependencyParsing "Input string here"')
    sys.exit()

doc = nlp(args[1])

displacy.serve(doc, style="dep")