from os import getenv
from dotenv import load_dotenv
from stanza import DownloadMethod
import logging

PROCESSORS = [
   "tokenize",
   "mwt",
   "ner",
   "pos",
   "depparse",
   "ner",
   "lemma"
   ]

def loadEnvironmentVariables() -> dict:
   """Function that loads all environment variables from a ".env" file or 
   the environment variables"""

   load_dotenv(dotenv_path="../data/.env")
   # Dict for return values
   global env
   env = {}

   # Take the environment variable, default to false
   # If the variable is "True", then True
   env['useREST'] = getenv("IG2USEREST", 'False') == 'True'
   # Take the environment variable, default to None
   env['useGPU'] = getenv("IG2USEGPU", None)
   if env['useGPU'] == "False":
      env['useGPU'] = False
   elif env['useGPU'] == "True":
      env['useGPU'] = True

   env['downloadMethod'] = getenv("IG2DLMETHOD", DownloadMethod.DOWNLOAD_RESOURCES)
   if env['downloadMethod'] == "reuse":
      env['downloadMethod'] = DownloadMethod.REUSE_RESOURCES
   elif env['downloadMethod'] == "none":
      env['downloadMethod'] = DownloadMethod.NONE

   env['logLevel'] = getenv("IG2STANZALOGLEVEL")

   env['displacyPort'] = int(getenv("IG2DISPLACYPORT", 5001))

   env['flaskPort'] = getenv("IG2FLASKPORT", 5000)

   logLevels = {"INFO":logging.INFO,
               "DEBUG":logging.DEBUG,
               "WARN":logging.WARNING,
               "ERROR":logging.ERROR,
               "CRITICAL":logging.CRITICAL,
               }

   env["logLevelFile"] = getenv("IG2LOGLEVELFILE")
   if env["logLevelFile"] in logLevels.keys():
      env["logLevelFile"] = logLevels[env["logLevelFile"]]
   else:
      env["logLevelFile"] = logging.DEBUG

   env["logLevelConsole"] = getenv("IG2LOGLEVELCONSOLE")
   if env["logLevelConsole"] in logLevels.keys():
      env["logLevelConsole"] = logLevels[env["logLevelConsole"]]
   else:
      env["logLevelConsole"] = logging.DEBUG

   env['coref'] = getenv("IG2COREF", True)
   if env['coref'] == "False":
      env['coref'] = False
   elif env['coref'] == "True":
      env['coref'] = True
   
   env['pipeline'] = getenv("IG2PIPELINE", "default_accurate")
   if env['pipeline'] in ["fast","accurate"]:
      env['pipeline'] = "default_"+env['pipeline']
   elif env['pipeline'] != "default":
      env['pipeline'] = "default_accurate"

   return env

def createLogger() -> None:
   """Creates a custom logger instance shared with all programs importing this file"""

   global logger

   logger = logging.getLogger(__name__)

   # Accept all logs
   logger.setLevel(logging.DEBUG)

   # Handlers for console and file output with separate logging levels
   fileHandler = logging.FileHandler("..\data\logs\log.log")
   consoleHandler = logging.StreamHandler()
   fileHandler.setLevel(env["logLevelFile"])
   consoleHandler.setLevel(env["logLevelConsole"])

   # Custom formatting for console and file output
   formatterFile = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',
                              '%d/%m/%Y %I:%M:%S %p')
   formatterConsole = logging.Formatter('%(levelname)s: %(message)s')
   consoleHandler.setFormatter(formatterConsole)
   fileHandler.setFormatter(formatterFile)

   # Add the custom handlers to the logger
   logger.addHandler(fileHandler)
   logger.addHandler(consoleHandler)

loadEnvironmentVariables()
createLogger()