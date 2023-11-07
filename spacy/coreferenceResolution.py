import spacy
import sys

# Load the pretrained model
nlp = spacy.load("en_coreference_web_trf")

# Take the system arguments
args = sys.argv

if len(args)<2:
    print('Error: a string must be passed with the function in the format:\ndependencyParsing "Input string here"')
    sys.exit()

doc = nlp(args[1])

print("Input text:\n",args[1])


print("Clusters and their corresponding spans: ")
for cluster in doc.spans:
    print(f"{cluster}: {doc.spans[cluster]}")
    for span in doc.spans[cluster]:
        print("Span: ",span,"span start: ", span.start, ". span end: ", span.end, ". ID: ", span.id, "Done")