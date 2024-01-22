package main

import (
	"IG-Parser-Stats/statistics"
	"flag"
	"fmt"
)

func main() {
	// Take parameters when running the application
	inputFile := flag.String("input", "input.json", "Input flag for input file")
	outputFile := flag.String("output", "output.json", "Output flag for output file")
	mode := flag.Int("mode", 0, "Mode flag for program mode, 0 for the autoRunner, 1 for the statistics runner\n"+
		"2 for the comparrison runner")

	flag.Parse()

	fmt.Println(*inputFile, *outputFile, *mode)

	switch *mode {
	case 0:
		statistics.AutoRunner(*inputFile, *outputFile)
	case 1:
		statistics.RunStatistics(*inputFile, *outputFile)
	case 2:
		statistics.Compare(*inputFile, *outputFile)
	case 3:
		statistics.ReverseAnnotation(*inputFile, *outputFile)
	}

	// If none found default to the autorunner with the default file path

	//statistics.RunStatistics()

	//statistics.AutoRunner()
}
