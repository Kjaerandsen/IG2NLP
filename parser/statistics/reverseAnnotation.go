package statistics

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// Constant for the removal of keywords based on character similarity.
// Atleas this amount of chars need to be equal for the words to be removed
const minWordLength = 3

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
		text = data[i].Manual
		text = removeSuffixes(text)

		outDataElement.Name = data[i].Name
		outDataElement.BaseTx = data[i].BaseTx
		outDataElement.Manual = data[i].Manual
		outDataElement.Stanza = data[i].Stanza
		outDataElement.ManualReversed = removeSymbols(text)
		outDataElement.StanzaReversed = removeSymbols(data[i].Stanza)

		var compStanza []string
		var compManual []string

		// Take the parsed sentences, split into []string by ""
		compStanza = strings.Split(outDataElement.StanzaReversed, " ")
		compManual = strings.Split(outDataElement.ManualReversed, " ")

		// Compare to the BaseText?

		// Compare to each other

		var j int
		var i int

		StanzaLen := len(compStanza)
		ManualLen := len(compManual)

		for j = 0; j < StanzaLen; j++ {
			fmt.Println(len(compStanza[j]), compStanza[j])
			if compStanza[j] == "" {
				fmt.Println("Removing thing", compStanza[j])
				compStanza = removeWord(compStanza, StanzaLen, j)
				StanzaLen--
				j--
			}
		}

		for i = 0; i < ManualLen; i++ {
			for j = 0; j < StanzaLen; j++ {
				// Remove empty "words"
				if compManual[i] == "" {
					compManual = removeWord(compManual, ManualLen, i)
					ManualLen--
					i--
					break
				} else if compManual[i] == compStanza[j] {

					// If the two words are equal then remove both from their arrays
					compManual = removeWord(compManual, ManualLen, i)

					compStanza = removeWord(compStanza, StanzaLen, j)

					ManualLen--
					StanzaLen--
					// Go through the new item at the same address from the start and check
					i--
					break
				}
			}
		}

		// Go through the remaining items,
		// check for edge cases where the punctuation spacing is improper
		// Or the difference is a beginning, ending or both char.
		for i = 0; i < ManualLen; i++ {
			for j = 0; j < StanzaLen; j++ {
				if j+1 < StanzaLen {
					if compManual[i] == compStanza[j]+compStanza[j+1] {
						// If the two words are equal then remove both from their arrays
						compManual = removeWord(compManual, ManualLen, i)

						if j < StanzaLen-1 {
							compStanza = append(compStanza[:j], compStanza[j+2:]...)
						} else {
							compStanza = compStanza[:j+1]
						}

						ManualLen--
						StanzaLen -= 2
						// Go through the new item at the same address from the start and check
						i--
						break
					}
				}
			}
		}

		// If the word of the stanza annotation is
		// a substring of the manual count them as the same word.
		for i = 0; i < StanzaLen; i++ {
			for j = 0; j < ManualLen; j++ {
				// If the word is a substring longer than the minimum
				if len(compStanza[i]) > minWordLength &&
					strings.Contains(compManual[j], compStanza[i]) {

					// If the two words are equal then remove both from their arrays
					compManual = removeWord(compManual, ManualLen, j)

					compStanza = removeWord(compStanza, StanzaLen, i)

					ManualLen--
					StanzaLen--
					// Go through the new item at the same address from the start and check
					i--
					break
					// If the word excluding the last char is a substring
				} else if strings.Contains(compManual[j], compStanza[i][:len(compStanza[i])-1]) &&
					len(compStanza[i][:len(compStanza[i])-1]) > minWordLength {

					fmt.Println("Match removing: ", compManual[j],
						compStanza[i][:len(compStanza[i])-1])

					// If the two words are equal then remove both from their arrays
					compManual = removeWord(compManual, ManualLen, j)

					compStanza = removeWord(compStanza, StanzaLen, i)

					ManualLen--
					StanzaLen--
					// Go through the new item at the same address from the start and check
					i--
					break
				}
			}
		}

		fmt.Println("Now displaying the two remaining string arrays:")
		fmt.Println("Manual difference:\n", compManual)
		fmt.Println("Automatic difference:\n", compStanza)

		outDataElement.ManualDifference = compManual
		outDataElement.StanzaDifference = compStanza

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

// Takes an array of words, the length and an id, removes the word with the id from the word array
func removeWord(words []string, wordLen, id int) []string {

	if id < wordLen {
		words = append(words[:id], words[id+1:]...)
	} else {
		words = words[:id]
	}

	return words
}