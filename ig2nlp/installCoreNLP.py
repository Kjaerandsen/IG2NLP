import stanza
import os

# Based on the instructions found at: https://stanfordnlp.github.io/stanza/client_setup.html
install_location = "./corenlp"
if not os.path.exists(install_location):
    os.makedirs(install_location)

stanza.install_corenlp(dir=install_location)

# After download set the CORENLP_HOME environment variable to the install location