class pipelineConfig:
   """Class for Stanza pipeline variables, used for pipeline initialization"""

   def __init__(self, tokenize:str="", mwt:str="", pos:str="", depparse:str="", lemma:str="", 
                ner:str="", coref:str="", constituency:str="") -> None:
      
      self.tokenize = tokenize
      self.mwt = mwt
      self.pos = pos
      self.depparse = depparse
      self.lemma = lemma
      self.ner = ner
      self.coref = coref
      self.constitutency = constituency

   def getProcessors(self) -> list[str]:
      """Creates a list of processors for the nlp pipeline 
      based on the provided processor configuration"""

      output:list[str] = []

      if self.tokenize      != "": output.append("tokenize")
      if self.mwt           != "": output.append("mwt")
      if self.pos           != "": output.append("pos")
      if self.depparse      != "": output.append("depparse")
      if self.lemma         != "": output.append("lemma")
      if self.ner           != "": output.append("ner")
      if self.coref         != "": output.append("coref")
      if self.constitutency != "": output.append("constituency")

      return output

   def getPackage(self) -> dict[str,str]:
      """Creates the package configuration for the nlp pipeline
      base on the provided processor configuration"""
      package:dict[str,str]=dict()

      if self.tokenize      != "": package["tokenize"]     = str(self.tokenize)
      if self.mwt           != "": package["mwt"]          = str(self.mwt)
      if self.pos           != "": package["pos"]          = str(self.pos)
      if self.depparse      != "": package["depparse"]     = str(self.depparse)
      if self.lemma         != "": package["lemma"]        = str(self.lemma)
      if self.ner           != "": package["ner"]          = str(self.ner)
      if self.coref         != "": package["coref"]        = str(self.coref)
      if self.constitutency != "": package["constituency"] = str(self.constitutency)

      return package