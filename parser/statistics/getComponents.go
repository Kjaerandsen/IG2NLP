package statistics

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// Function to retrieve all symbols from annotated statements
func GetComponents(file string, outFile string) {
	// Read the input file
	content, err := os.ReadFile(file)
	if err != nil {
		fmt.Println("Error reading file:", err)
		return
	}

	var data inputStructureGeneric

	err = json.Unmarshal(content, &data)
	if err != nil {
		fmt.Println("Error unmarshalling JSON:", err)
		return
	}

	fmt.Println(len(data))

	for i := 0; i < len(data); i++ {
		fmt.Println("\nParsing statement: ", i, " ", data[i].Name)

		var stats StatisticsGeneric

		// Get the statistics from the manually parsed statement
		stats, success := componentHandler(data[i].ManuTx, false)
		if success {
			data[i].ManualParsed = stats
		}

		// Get the statistics from the automatically parsed statement
		stats, success = componentHandler(data[i].AutoTx, true)
		if success {
			data[i].StanzaParsed = stats
		}
	}

	// Convert the struct to JSON
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		fmt.Println("Error marshalling JSON:", err)
		return
	}

	// Write the JSON data to the file
	err = os.WriteFile(outFile, jsonData, 0644)
	if err != nil {
		fmt.Println("Error writing to file:", err)
		return
	}
}

func componentHandler(inputStatement string, split bool) (StatisticsGeneric, bool) {
	var output StatisticsGeneric
	var nestedComponents []JSONComponent
	var sentences []string

	//TODO: Maybe reconsider the splitting functionality as the custom parsing does not rely on
	// individual sentences
	// If split, split the inputStatement into individual sentences using "."
	// Then recurse with split set to false
	if split {
		//sentences = strings.Split(inputStatement, ".")
		sentences = append(sentences, inputStatement)

		//print(sentences[0])
	start:
		for i := 0; i < len(sentences); i++ {
			if len(sentences[i]) == 0 {
				if i+1 < len(sentences) {
					sentences = append(sentences[:i], sentences[i+1:]...)
					break start
				} else {
					sentences = sentences[:i]
				}
			}
		}

		for i := 0; i < len(sentences); i++ {
			response, _ := componentHandler(sentences[i], false)

			output = combineStatisticsGeneric(response, output)
		}
		//fmt.Println(output.Components)
		// Else get the components
	} else {
		// Get all components with nesting (i.e. Cac{...})
		// Count them and remove their contents (statistics without nesting)
		// Get all components with nesting
		//fmt.Println("inputStatement is: ", inputStatement)
		result, inputStatement := getNestedComponentsGeneric(inputStatement)
		nestedComponents = append(nestedComponents, result...)

		// Go through all nested components detected
		for i := 0; i < len(nestedComponents); i++ {
			// If the type is within the ComponentNames add the component to the matched component type
			for j := 0; j < len(NestedComponentNames); j++ {
				if nestedComponents[i].ComponentType == ComponentNames[j] {
					output.Components[j] = append(output.Components[j], nestedComponents[i])
					output.Count[j]++
				}
			}
		}
		// Get all components without nesting
		//fmt.Println("inputStatement is: ", inputStatement)
		output = findSymbolsGeneric(inputStatement)

		// Count occurrences of logical operators
		output.Count[17] += strings.Count(inputStatement, "[OR]")
		output.Count[18] += strings.Count(inputStatement, "[XOR]")
		output.Count[19] += strings.Count(inputStatement, "[AND]")

	}
	return output, true
}

// Takes a string, returns a JSON object with all the components ordered, and counts of each component.
func findSymbolsGeneric(text string) StatisticsGeneric {
	fmt.Println("Running findSymbols on: ", text)

	var output StatisticsGeneric
	var result Statistics

	// Set the logical operator counts
	output.Count[17] = strings.Count(text, "[AND]")
	output.Count[18] = strings.Count(text, "[OR]")
	output.Count[19] = strings.Count(text, "[XOR]")

	// Remove the logical operators
	text = strings.ReplaceAll(text, "[OR]", "or")
	text = strings.ReplaceAll(text, "[XOR]", "or")
	text = strings.ReplaceAll(text, "[AND]", "and")

	// Find and add all components
	for i := 0; i < 17; i++ {
		fmt.Println("Doing component: ", ComponentNames[i])
		result, _ = getComponentOccurrances(text, ComponentNames[i])

		// Add the new components to the output
		output.Count[i] += len(result.Components)
		output.Components[i] = append(output.Components[0], result.Components...)
	}

	fmt.Println(output)

	return output
}
