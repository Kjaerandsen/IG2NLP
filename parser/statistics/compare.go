package statistics

import (
	"encoding/json"
	"fmt"
	"os"
)

func CompareParsed(inputFile string, outputFile string) {
	content, err := os.ReadFile(inputFile)
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

	var outData []CompareStatisticsGeneric

	fmt.Println(len(data))

	for i := 0; i < len(data); i++ {
		outData = append(outData, *new(CompareStatisticsGeneric))
		outData[i].Manual = data[i].Manual
		outData[i].Stanza = data[i].Stanza
		outData[i].BaseTx = data[i].BaseTx
		outData[i].Count[0] = data[i].ManualParsed.Count
		outData[i].Count[1] = data[i].StanzaParsed.Count

		// Look for true positives
		CompareComponentsDirect(&data[i].ManualParsed, &data[i].StanzaParsed, &outData[i])
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

// Function that compares the reversed text of both the manual and automatic annotations
func CompareReversedText() {

}

// Function that compares the component contents of both the manual and automatic annotations
func CompareComponents() {

}

// For 1-to-1 comparrison, where the string contents are equal.
// Removes all equal components and counts up a true positive rate.
func CompareComponentsDirect(Manual *StatisticsGeneric, Automatic *StatisticsGeneric, outData *CompareStatisticsGeneric) {

	for i := 0; i < len(ComponentNames); i++ {
		outData.TP[i], Manual.Components[i], Automatic.Components[i] =
			CompareComponentTP(Manual.Components[i], Automatic.Components[i], len(Manual.Components[i]), len(Automatic.Components[i]))
		// Reduce the count
		outData.Count[0][i] -= outData.TP[i]
		outData.Count[1][i] -= outData.TP[i]
	}

	outData.ExtraComponents[0] = Manual.Components
	outData.ExtraComponents[1] = Automatic.Components
}

// Function that takes two lists of components and compares the contents to find true positive content matches
func CompareComponentTP(list1 []JSONComponent, list2 []JSONComponent, list1Len, list2Len int) (int, []JSONComponent, []JSONComponent) {

	TPCount := 0
	fmt.Println(list1Len, list2Len)
	for i := 0; i < list1Len; i++ {
		for j := 0; j < list2Len; j++ {
			fmt.Println("Going")
			// If match
			if list1[i].Content == list2[j].Content {
				fmt.Println("Content match")
				// If the two words are equal then remove both from their arrays
				list1 = removeComponentList(list1, list1Len, i)
				list2 = removeComponentList(list2, list2Len, j)

				// Reduce the length counters by one
				list1Len--
				list2Len--

				// Add to the true positive count
				TPCount++

				// Go through the new item at the same address from the start and check
				i--
				break
			}
		}
	}

	return TPCount, list1, list2
}

// Takes an array of words, the length and an id, removes the word with the id from the word array
func removeComponentList(components []JSONComponent, compLen, id int) []JSONComponent {

	if id < compLen {
		components = append(components[:id], components[id+1:]...)
	} else {
		components = components[:id]
	}

	return components
}
