import stanza
from stanza.server import CoreNLPClient
import sys

# Runs using the coreNLP client of stanza
# Based on the instructions at https://stanfordnlp.github.io/stanza/client_setup.html
corenlp_dir = './corenlp'
stanza.install_corenlp(dir=corenlp_dir)

client = CoreNLPClient(
    annotators=["coref"], 
    memory='4G', 
    endpoint='http://localhost:9001',
    be_quiet=True)
print(client)
# Set the CORENLP_HOME environment variable to point to the installation location

# Take the system arguments
args = sys.argv

if len(args)<2:
    print('Error: a string must be passed with the function in the format:\n' + 
          'dependencyParsing "Input string here"')
    sys.exit()

client.start()
# Wait for the server to start
import time; time.sleep(10)

doc = client.annotate(args[1])
print(type(doc))

print('\nNow printing coref tree\n')

#for sentence in doc.sentence:
#    print("\n\n NEW SENTENCE: ")
#    print(sentence.mentionsForCoref)

for chains in doc.corefChain:
    print("\n\n Coref chains: ")
    print(chains)

for sentence in doc.sentence:
    for token in sentence.token:
        #print(token)
        print(token.word)
        print(token.tokenBeginIndex)
        print(token.tokenEndIndex)