package statistics

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
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
	var jsonData []byte

	fmt.Println(len(data))

	for i := 0; i < len(data); i++ {
		outData = append(outData, *new(CompareStatisticsGeneric))
		outData[i].Manual = data[i].Manual
		outData[i].Stanza = data[i].Stanza
		outData[i].BaseTx = data[i].BaseTx
		outData[i].Count[0] = data[i].ManualParsed.Count
		outData[i].Count[1] = data[i].StanzaParsed.Count

		// Look for true positives
		CompareComponentsDirect(&data[i].ManualParsed, &data[i].StanzaParsed,
			&outData[i])
		// Look for partial positives
		outData[i] = CompareComponentsPartial(outData[i])
	}

	// Convert output data type
	var outputData []CompareOut
	for i := 0; i < len(data); i++ {
		var newOutput CompareOut

		newOutput.BaseTx = outData[i].BaseTx
		newOutput.Manual = outData[i].Manual
		newOutput.Stanza = outData[i].Stanza

		// Add all extra components
		for j := 0; j < 17; j++ {
			// Add the manual extra components
			newOutput.ExtraComponents[0] = append(newOutput.ExtraComponents[0],
				outData[i].ExtraComponents[0][j]...)
			// Add the automatic extra components
			newOutput.ExtraComponents[1] = append(newOutput.ExtraComponents[1],
				outData[i].ExtraComponents[1][j]...)
		}

		// Handle the counts
		newOutput.Count.AttributeProperty =
			[5]int{
				outData[i].TP[0],           // TP
				outData[i].PartialCount[0], // PP
				outData[i].Count[1][0],     // FP
				outData[i].Count[0][0],     // FN
				outData[i].TP[0] + outData[i].PartialCount[0] +
					outData[i].Count[1][0] + outData[i].Count[0][0]}

		newOutput.Count.DirectObject =
			[5]int{
				outData[i].TP[1],
				outData[i].PartialCount[1],
				outData[i].Count[1][1],
				outData[i].Count[0][1],
				outData[i].TP[1] + outData[i].PartialCount[1] +
					outData[i].Count[1][1] + outData[i].Count[0][1]}

		newOutput.Count.DirectObjectProperty =
			[5]int{
				outData[i].TP[2],
				outData[i].PartialCount[2],
				outData[i].Count[1][2],
				outData[i].Count[0][2],
				outData[i].TP[2] + outData[i].PartialCount[2] +
					outData[i].Count[1][2] + outData[i].Count[0][2]}

		newOutput.Count.IndirectObject =
			[5]int{
				outData[i].TP[3],
				outData[i].PartialCount[3],
				outData[i].Count[1][3],
				outData[i].Count[0][3],
				outData[i].TP[3] + outData[i].PartialCount[3] +
					outData[i].Count[1][3] + outData[i].Count[0][3]}

		newOutput.Count.IndirectObjectProperty =
			[5]int{
				outData[i].TP[4],
				outData[i].PartialCount[4],
				outData[i].Count[1][4],
				outData[i].Count[0][4],
				outData[i].TP[4] + outData[i].PartialCount[4] +
					outData[i].Count[1][4] + outData[i].Count[0][4]}

		newOutput.Count.ActivationCondition =
			[5]int{
				outData[i].TP[5],
				outData[i].PartialCount[5],
				outData[i].Count[1][5],
				outData[i].Count[0][5],
				outData[i].TP[5] + outData[i].PartialCount[5] +
					outData[i].Count[1][5] + outData[i].Count[0][5]}

		newOutput.Count.ExecutionConstraint =
			[5]int{
				outData[i].TP[6],
				outData[i].PartialCount[6],
				outData[i].Count[1][6],
				outData[i].Count[0][6],
				outData[i].TP[6] + outData[i].PartialCount[6] +
					outData[i].Count[1][6] + outData[i].Count[0][6]}

		newOutput.Count.ConstitutedEntityProperty =
			[5]int{
				outData[i].TP[7],
				outData[i].PartialCount[7],
				outData[i].Count[1][7],
				outData[i].Count[0][7],
				outData[i].TP[7] + outData[i].PartialCount[7] +
					outData[i].Count[1][7] + outData[i].Count[0][7]}

		newOutput.Count.ConstitutingProperties =
			[5]int{
				outData[i].TP[8],
				outData[i].PartialCount[8],
				outData[i].Count[1][8],
				outData[i].Count[0][8],
				outData[i].TP[8] + outData[i].PartialCount[8] +
					outData[i].Count[1][8] + outData[i].Count[0][8]}

		newOutput.Count.ConstitutingPropertiesProperties =
			[5]int{
				outData[i].TP[9],
				outData[i].PartialCount[9],
				outData[i].Count[1][9],
				outData[i].Count[0][9],
				outData[i].TP[9] + outData[i].PartialCount[9] +
					outData[i].Count[1][9] + outData[i].Count[0][9]}

		newOutput.Count.OrElse =
			[5]int{
				outData[i].TP[10],
				outData[i].PartialCount[10],
				outData[i].Count[1][10],
				outData[i].Count[0][10],
				outData[i].TP[10] + outData[i].PartialCount[10] +
					outData[i].Count[1][10] + outData[i].Count[0][10]}

		newOutput.Count.Attribute =
			[5]int{
				outData[i].TP[11],
				outData[i].PartialCount[11],
				outData[i].Count[1][11],
				outData[i].Count[0][11],
				outData[i].TP[11] + outData[i].PartialCount[11] +
					outData[i].Count[1][11] + outData[i].Count[0][11]}

		newOutput.Count.Deontic =
			[5]int{
				outData[i].TP[12],
				outData[i].PartialCount[12],
				outData[i].Count[1][12],
				outData[i].Count[0][12],
				outData[i].TP[12] + outData[i].PartialCount[12] +
					outData[i].Count[1][12] + outData[i].Count[0][12]}

		newOutput.Count.Aim =
			[5]int{
				outData[i].TP[13],
				outData[i].PartialCount[13],
				outData[i].Count[1][13],
				outData[i].Count[0][13],
				outData[i].TP[13] + outData[i].PartialCount[13] +
					outData[i].Count[1][13] + outData[i].Count[0][13]}

		newOutput.Count.ConstitutedEntity =
			[5]int{
				outData[i].TP[14],
				outData[i].PartialCount[14],
				outData[i].Count[1][14],
				outData[i].Count[0][14],
				outData[i].TP[14] + outData[i].PartialCount[14] +
					outData[i].Count[1][14] + outData[i].Count[0][14]}

		newOutput.Count.Modal =
			[5]int{
				outData[i].TP[15],
				outData[i].PartialCount[15],
				outData[i].Count[1][15],
				outData[i].Count[0][15],
				outData[i].TP[15] + outData[i].PartialCount[15] +
					outData[i].Count[1][15] + outData[i].Count[0][15]}

		newOutput.Count.ConstitutiveFunction =
			[5]int{
				outData[i].TP[16],
				outData[i].PartialCount[16],
				outData[i].Count[1][16],
				outData[i].Count[0][16],
				outData[i].TP[16] + outData[i].PartialCount[16] +
					outData[i].Count[1][16] + outData[i].Count[0][16]}

		newOutput.ORCount[0] = outData[i].Count[0][17]
		newOutput.ORCount[1] = outData[i].Count[1][17]
		newOutput.XORCount[0] = outData[i].Count[0][18]
		newOutput.XORCount[1] = outData[i].Count[1][18]
		newOutput.ANDCount[0] = outData[i].Count[0][19]
		newOutput.ANDCount[1] = outData[i].Count[1][19]

		outputData = append(outputData, newOutput)

	}

	// Convert the struct to JSON
	jsonData, err = json.MarshalIndent(outputData, "", "  ")
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

// Function that compares the reversed text of both the manual and
// automatic annotations
func CompareReversedText() {

}

// Function that compares the component contents of both the manual
// and automatic annotations
func CompareComponents() {

}

func CompareComponentsPartial(data CompareStatisticsGeneric) CompareStatisticsGeneric {
	// Compare the components in the extraComponents pool

	// First by certain components
	// X - X, X,p - X
	for i := 0; i < 17; i++ {
		manualLen := len(data.ExtraComponents[0][i])
		automaLen := len(data.ExtraComponents[1][i])
		for j := 0; j < manualLen; j++ {
			for k := 0; k < automaLen; k++ {
				if j == manualLen || k == automaLen {
					break
				}
				manualContent := data.ExtraComponents[0][i][j].Content
				automaContent := data.ExtraComponents[1][i][k].Content

				// If the content is a match, then the nesting was incorrect
				if manualContent == automaContent {
					// Content match
					var match PartialPool
					// Add the match to a PartialPool
					match.ManualComponents =
						append(match.ManualComponents, data.ExtraComponents[0][i][j])
					match.StanzaComponents =
						append(match.StanzaComponents, data.ExtraComponents[1][i][k])
					// Append the PartialPool to the data
					data.PartialPool = append(data.PartialPool, match)
					// Update the counters
					data.Count[0][i]--
					data.Count[1][i]--
					data.PartialCount[i]++
					// Remove the elements from the original data
					data.ExtraComponents[0][i] =
						append(data.ExtraComponents[0][i][:j],
							data.ExtraComponents[0][i][j+1:]...)
					data.ExtraComponents[1][i] =
						append(data.ExtraComponents[1][i][:k],
							data.ExtraComponents[1][i][k+1:]...)
					// Reduce the second counter to go through the rest of the components
					k--
					automaLen--
					manualLen--
					continue
				}

				// Check for partial matches
				// If the automatic is contained within the manual
				if strings.Contains(manualContent, automaContent) {
					// Partial match
					var match PartialPool
					// Add the match to a PartialPool
					match.ManualComponents =
						append(match.ManualComponents, data.ExtraComponents[0][i][j])
					match.StanzaComponents =
						append(match.StanzaComponents, data.ExtraComponents[1][i][k])
					// Append the PartialPool to the data
					data.PartialPool = append(data.PartialPool, match)
					// Update the counters
					data.Count[0][i]--
					data.Count[1][i]--
					data.PartialCount[i]++
					// Remove the elements from the original data
					data.ExtraComponents[0][i] =
						append(data.ExtraComponents[0][i][:j], data.ExtraComponents[0][i][j+1:]...)
					data.ExtraComponents[1][i] =
						append(data.ExtraComponents[1][i][:k], data.ExtraComponents[1][i][k+1:]...)
					// Reduce the second counter to go through the rest of the components
					k--
					automaLen--
					manualLen--
					continue
				}
				// If the manual is contained within the automatic
				if strings.Contains(automaContent, manualContent) {
					// Partial match
					var match PartialPool
					// Add the match to a PartialPool
					match.ManualComponents =
						append(match.ManualComponents, data.ExtraComponents[0][i][j])
					match.StanzaComponents =
						append(match.StanzaComponents, data.ExtraComponents[1][i][k])
					// Append the PartialPool to the data
					data.PartialPool = append(data.PartialPool, match)
					// Update the counters
					data.Count[0][i]--
					data.Count[1][i]--
					data.PartialCount[i]++
					// Remove the elements from the original data
					data.ExtraComponents[0][i] =
						append(data.ExtraComponents[0][i][:j], data.ExtraComponents[0][i][j+1:]...)
					data.ExtraComponents[1][i] =
						append(data.ExtraComponents[1][i][:k], data.ExtraComponents[1][i][k+1:]...)
					// Reduce the second counter to go through the rest of the components
					k--
					automaLen--
					manualLen--
					continue
				}
			}
		}
	}
	// Cac - Cex, Attribute - X and finally X - Y

	// Comparrison first by words, if word is contained then add both to the pool

	// If match X - X add both to a partial pool, remove one from each Count
	// Add 1 to the PartialCount of that symbol
	// Then look for other components with the rest of the words
	return data
}

// For 1-to-1 comparrison, where the string contents are equal.
// Removes all equal components and counts up a true positive rate.
func CompareComponentsDirect(Manual *StatisticsGeneric, Automatic *StatisticsGeneric,
	outData *CompareStatisticsGeneric) {

	for i := 0; i < len(ComponentNames); i++ {
		outData.TP[i], Manual.Components[i], Automatic.Components[i] =
			CompareComponentTP(Manual.Components[i], Automatic.Components[i],
				len(Manual.Components[i]), len(Automatic.Components[i]))
		// Reduce the count
		outData.Count[0][i] -= outData.TP[i]
		outData.Count[1][i] -= outData.TP[i]
	}

	outData.ExtraComponents[0] = Manual.Components
	outData.ExtraComponents[1] = Automatic.Components
}

// Function that takes two lists of components and compares the contents
// to find true positive content matches
func CompareComponentTP(list1, list2 []JSONComponent, list1Len, list2Len int) (
	int, []JSONComponent, []JSONComponent) {

	TPCount := 0
	for i := 0; i < list1Len; i++ {
		for j := 0; j < list2Len; j++ {
			// If content match and equal nesting
			if list1[i].Content == list2[j].Content && list1[i].Nested == list2[j].Nested {
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
