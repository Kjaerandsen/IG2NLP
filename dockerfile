FROM python:3.11
#VOLUME stanza_resources

RUN pip install --upgrade pip

#Create custom stanza_resources directory
#ENV STANZA_RESOURCES_DIR /stanza_resources
#RUN mkdir ./stanza_resources
#RUN mkdir ./stanza_resources/en
COPY ./ig2nlp ./ig2nlp
#Use the local data directory
#COPY ./data ./data
#Alternatively, create a new data directory for the container
#RUN mkdir ./data
#RUN mkdir ./data/logs
WORKDIR /ig2nlp

RUN pip install --no-cache-dir -r requirements.txt

#Download all fast models
#RUN wget https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main/resources_1.7.0.json -O /stanza_resources/resources.json
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/tokenize/combined.pt -P /stanza_resources/en/tokenize/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/mwt/combined.pt -P /stanza_resources/en/mwt/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/pos/combined_nocharlm.pt -P /stanza_resources/en/pos/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/depparse/combined_nocharlm.pt -P /stanza_resources/en/depparse/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/lemma/combined_nocharlm.pt -P /stanza_resources/en/lemma/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/ner/ontonotes-ww-multi_nocharlm.pt -P /stanza_resources/en/ner/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/pretrain/conll17.pt -P /stanza_resources/en/pretrain/
#RUN wget https://huggingface.co/stanfordnlp/stanza-en/resolve/v1.7.0/models/backward_charlm/1billion.pt -P /stanza_resources/en/pretrain/

EXPOSE 5000

CMD [ "python", "api.py" ]
#CMD [ "sleep", "infinity" ]