package main

import (
	"IG-Parser-Stats/statistics"
	"flag"
	"fmt"
)

func main() {
	// Take parameters when running the application
	inputFile := flag.String("i", "input", "Input flag for input file")
	outputFile := flag.String("o", "output", "Output flag for output file")
	mode := flag.Int("mode", 0,
		"Mode flag for program mode, 0 for the autoRunner, 1 for the statistics runner\n"+
			"2 for the comparrison runner")

	flag.Parse()

	fmt.Println(*inputFile, *outputFile, *mode)

	*inputFile = "../data/" + *inputFile
	*outputFile = "../data/" + *outputFile

	// If none found default to the autorunner with the default file path
	switch *mode {
	case 0:
		statistics.AutoRunnerGeneric(
			*inputFile+statistics.FILETYPE,
			*outputFile+statistics.FILETYPE)
	case 1:
		statistics.GetComponents(
			*inputFile+statistics.FILETYPE,
			*outputFile+statistics.FILETYPE)
	case 2:
		statistics.CompareParsed(
			*inputFile,
			*outputFile)
	case 3:
		statistics.ReverseAnnotation(
			*inputFile+statistics.FILETYPE,
			*outputFile+statistics.FILETYPE)
	}

	//statistics.RunStatistics()

	//statistics.AutoRunner()
}
