import spacy
from spacy import displacy
import sys
import pandas as pd

# Load the pretrained model
nlp = spacy.load("en_core_web_sm")
# Take the system arguments
args = sys.argv

# Check if an input was given
if len(args)<2:
    print('Error: a string must be passed with the function in the format:\ndependencyParsing "Input string here"')
    sys.exit()

# Take the input string
doc = nlp(args[1])

# Create a table with the relevant information from the doc
df = pd.DataFrame(columns=["Token", "Lemma", "POS", "Tag", "Dependency", "Entity"])
for token in doc:
    df = df._append({"Token": token.text, "Lemma":token.lemma_, "POS": token.pos_, "Tag": token.tag_, "Dependency": token.dep_, 
                    "Entity": token.ent_type_}, ignore_index=True)

print(df)

# Spin up a webserver on port 5000 with the dependency tree using displacy
displacy.serve(doc, style="dep")