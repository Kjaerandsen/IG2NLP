import json
import argparse

from utility.comparison import *
from utility.componentStatistics import *

def main() -> None:
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", 
      help="input file, defaults to json extension, i.e. input is treated as input.json")
   parser.add_argument("-o", "--output", 
      help="output file, defaults to json extension, i.e. output is treated as output.json")
   parser.add_argument("-m", "--mode",
      help="mode of the program, defaults to the whole testing pipline ignoring nesting. For more info\
   refer to the readme file.", default=30, type=int)
   parser.add_argument("-n", "--nested",
      help="nesting toggle, defaults to not handling components nested within other components.", 
      action='store_true')
   args = parser.parse_args()

   if not args.input:
      filename = "../data/output.json"
   else:
      filename = "../data/"+args.input+".json"

   if not args.output:
      outfilename = "../data/output"
   else:
      outfilename = "../data/"+args.output

   mode = args.mode

   with open(filename, "r") as input:
      jsonData = json.load(input)

   match mode:
      case 0:
         # Call case 1, then read the output data as the input for case 2
         components(jsonData, outfilename, args.nested)
         with open(outfilename+".json", "r") as input:
            jsonData = json.load(input)
         compare(jsonData, outfilename+"Comp")
      case 1:
         components(jsonData, outfilename, args.nested)
      case 2:
         compare(jsonData, outfilename)

main()