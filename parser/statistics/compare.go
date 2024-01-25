package statistics

import (
	"encoding/json"
	"fmt"
	"os"
)

func Compare(inputFile string, outputFile string) {
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

	var outData []StatisticsCompare

	fmt.Println(len(data))

	for i := 0; i < len(data); i++ {
		//var stats Statistics

		outData = append(outData, *new(StatisticsCompare))
		//stats = findSymbols(data[i].ProcessedText)
		outData[i].Manual = data[i].Manual
		outData[i].Stanza = data[i].Stanza
		outData[i].BaseTx = data[i].BaseTx

		outData[i].AProperty = data[i].ManualParsed.AttributePropertyCount -
			data[i].StanzaParsed.AttributePropertyCount

		outData[i].AttributeCount = data[i].ManualParsed.AttributePropertyCount

		outData[i].BdirProperty = data[i].ManualParsed.DirectObjectPropertyCount -
			data[i].StanzaParsed.DirectObjectPropertyCount

		outData[i].DirectObjectCount = data[i].ManualParsed.DirectObjectPropertyCount

		outData[i].BindProperty = data[i].ManualParsed.IndirectObjectPropertyCount -
			data[i].StanzaParsed.IndirectObjectPropertyCount

		outData[i].IndirectObjectCount = data[i].ManualParsed.IndirectObjectPropertyCount

		/*
			stats, success = findSymbols(data[i].Spacy)
			if success {
				data[i].SpacyParsed = stats
			}
		*/

		//stats = findSymbols(data[i].Stanza)
		//data[i].StanzaParsed = stats
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
