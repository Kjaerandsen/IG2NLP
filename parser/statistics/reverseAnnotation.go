package statistics

import (
	"encoding/json"
	"fmt"
	"os"
)

func ReverseAnnotation(inputFile string, outputFile string) {
	content, err := os.ReadFile(inputFile)
	if err != nil {
		fmt.Println("Error reading file:", err)
		return
	}

	var data inputStructure

	err = json.Unmarshal(content, &data)
	if err != nil {
		fmt.Println("Error unmarshalling JSON:", err)
		return
	}

	fmt.Println(len(data))

	var outData []textComparison
	var text string

	for i := 0; i < len(data); i++ {
		var outDataElement textComparison
		// Remove Suffixes from the manually annotated text
		text = data[i].ProcessedText
		text = removeSuffixes(text)

		outDataElement.Name = data[i].Name
		outDataElement.BaseText = data[i].BaseText
		outDataElement.ProcessedText = data[i].ProcessedText
		outDataElement.Stanza = data[i].Stanza
		outDataElement.ProcessedTextReversed = removeSymbols(text)
		outDataElement.StanzaReversed = removeSymbols(data[i].Stanza)

		outData = append(outData, outDataElement)
	}

	// Convert the struct to JSON
	jsonData, err := json.MarshalIndent(outData, "", "  ")
	if err != nil {
		fmt.Println("Error marshalling JSON:", err)
		return
	}

	// Write the JSON data to the file
	err = os.WriteFile(outputFile, jsonData, 0644)
	if err != nil {
		fmt.Println("Error writing to file:", err)
		return
	}
}
