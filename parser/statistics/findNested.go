package statistics

import (
	"fmt"
	"log"
	"regexp"
	"strings"
)

//"Somethignn Cac[afwfawfw]{A(something else) I(Something) Bdir{Nested} Cac(This is another)}", "Cac"
//Somethignn Cac[afwfawfw]{something Cacelse Something Nested his is another}

// Takes a statement in the form of a string, goes through and removes all IG Script notation syntax
func removeSymbols(text string) string {

	// Remove all semantic annotations
	for i := 0; i < 17; i++ {
		//fmt.Println("Doing component: ", ComponentNames[i])
		text = removeComponent(text, ComponentNames[i])
	}

	text = strings.ReplaceAll(text, "[OR]", "or")
	text = strings.ReplaceAll(text, "[XOR]", "or")
	text = strings.ReplaceAll(text, "[AND]", "and")

	return text
}

// Takes a string and a component, removes all instances of that component from the string
func removeComponent(text string, component string) string {
	componentLength := len(component)
	componentContents := ""
	position := 0
	// Find the first component
	position = strings.Index(text, component)

	for position != -1 {

		//fmt.Println("Found component: ", position)

		// Update the start of the symbol, used for removing it later
		start := position

		// Set the position to the start of the brackets for the symbol
		position = position + componentLength

		// Set the end position of the symbol, used for removing the brackets later
		end := 0

		//fmt.Println(text[position : position+1])
		//fmt.Println(text)

		// If semantic annotation move the position to the end of the annotation
		if text[position] == '[' {
			//fmt.Println("Found Semantic annotation")
			position = strings.Index(text[position:], "]") + position + 1
		}

		// Check if the symbol is a nested symbol
		if text[position:position+1] == "{" {
			//fmt.Println("Nested")
			// Find the scope of the component contents
			brackets := 1

			for i := position + 1; i < len(text); i++ {
				if text[i] == byte('{') {
					brackets++
				} else if text[i] == byte('}') {
					brackets--
				}
				if brackets == 0 {
					componentContents = text[position+1 : i]
					end = i
					//fmt.Println("Component contents: ", componentContents)
					break
				}
			}

			if brackets != 0 {
				log.Fatal("Could not find escape bracket, ", text)
				break
			}

			// Replace the component with its contents
			text = text[:start] + componentContents + text[end+1:]
			//fmt.Println("Replaced text contents: ", text)
			// Find the next component
			strings.Index(text, component)

			position = strings.Index(text, component)

			// Check if the symbol is a non-nested symbol
		} else if text[position:position+1] == "(" {
			//fmt.Println("Not Nested")
			// Find the scope of the component contents
			brackets := 1

			for i := position + 1; i < len(text); i++ {
				if text[i] == byte('(') {
					brackets++
				} else if text[i] == byte(')') {
					brackets--
				}
				if brackets == 0 {
					componentContents = text[position+1 : i]
					end = i
					//fmt.Println("Component contents: ", componentContents)
					break
				}
			}

			if brackets != 0 {
				log.Fatal("Could not find escape bracket, ", text)
				break
			}

			// Replace the component with its contents
			text = text[:start] + componentContents + text[end+1:]
			//fmt.Println("Replaced text contents: ", text)
			// Find the next component
			strings.Index(text, component)

			position = strings.Index(text, component)

			// If the symbol is a false positive recurse over the rest of the text until done
		} else {
			// Run the same function for the rest of the text recursively until complete
			text = text[:position+componentLength] +
				removeComponent(text[position+componentLength:], component)
			return text
		}
	}

	// Another alternative is to try to run the sentences through a
	// pos-tagger to remove punctuation from the equation

	// Return the parsed text with all instances of the symbol removed,
	// maintaining the contents of the symbols
	return text
}

// Takes a string and a component, removes all instances of that component from the string
func getComponentOccurrances(text string, component string) (Statistics, string) {
	var output Statistics

	var componentOccurrance JSONComponent

	componentOccurrance.ComponentType = component

	componentLength := len(component)
	componentContents := ""
	position := 0
	// Find the first component
	position = strings.Index(text, component)

	for position != -1 {

		fmt.Println("Found component: ", position)

		// Update the start of the symbol, used for removing it later
		start := position

		// Set the position to the start of the brackets for the symbol
		position = position + componentLength

		// Set the end position of the symbol, used for removing the brackets later
		end := 0

		fmt.Println(text[position : position+1])
		fmt.Println(text)

		componentOccurrance.SemanticAnnotation = ""

		// If semantic annotation move the position to the end of the annotation
		if text[position] == '[' {
			fmt.Println("Found Semantic annotation", position)

			positionEnd := strings.Index(text[position:], "]") + position

			fmt.Println(position+1, positionEnd)
			// Set the semantic annotation
			componentOccurrance.SemanticAnnotation = text[position+1 : positionEnd]

			// Update the position to start the parsing the contents of the component
			position = positionEnd + 1
		}

		fmt.Println("Done with semantic annotation")

		// Check if the symbol is a nested symbol
		if text[position:position+1] == "{" {
			fmt.Println("Nested")
			componentOccurrance.Nested = true
			// Find the scope of the component contents
			brackets := 1

			componentOccurrance.StartID = position + 1

			for i := position + 1; i < len(text); i++ {
				if text[i] == byte('{') {
					brackets++
				} else if text[i] == byte('}') {
					brackets--
				}
				if brackets == 0 {
					componentContents = text[position+1 : i]
					end = i
					fmt.Println("Component contents: ", componentContents)
					componentOccurrance.Content = removeSymbols(componentContents)
					break
				}
			}

			if brackets != 0 {
				log.Fatal("Could not find escape bracket, ", text)
				break
			}

			output.Components = append(output.Components, componentOccurrance)

			// Replace the component with its contents
			text = text[:start] + componentContents + text[end+1:]
			fmt.Println("Replaced text contents: ", text)
			// Find the next component
			strings.Index(text, component)

			position = strings.Index(text, component)

			// Check if the symbol is a non-nested symbol
		} else if text[position:position+1] == "(" {
			fmt.Println("Not Nested")
			componentOccurrance.Nested = false
			// Find the scope of the component contents
			brackets := 1

			componentOccurrance.StartID = position + 1

			for i := position + 1; i < len(text); i++ {
				if text[i] == byte('(') {
					brackets++
				} else if text[i] == byte(')') {
					brackets--
				}
				if brackets == 0 {
					componentContents = text[position+1 : i]
					end = i
					fmt.Println("Component contents: ", componentContents)
					componentOccurrance.Content = componentContents
					break
				}
			}

			if brackets != 0 {
				log.Fatal("Could not find escape bracket, ", text)
				break
			}

			output.Components = append(output.Components, componentOccurrance)

			// Replace the component with its contents
			text = text[:start] + componentContents + text[end+1:]
			fmt.Println("Replaced text contents: ", text)
			// Find the next component
			strings.Index(text, component)

			position = strings.Index(text, component)

			// If the symbol is a false positive recurse over the rest of the text until done
		} else {
			// Run the same function for the rest of the text recursively until complete
			result, _ := getComponentOccurrances(text[position+componentLength:], component)

			// Update the start position for each component to take into account the substring used
			for j := 0; j < len(result.Components); j++ {
				result.Components[j].StartID = result.Components[j].StartID +
					position + componentLength + 1
			}

			// Add the resulting components
			output.Components = append(output.Components, result.Components...)
			// Return the retreived components
			return output, text
		}
	}

	// Return the retrieved components
	return output, text
}

func findNestedPart(text string, component string) []JSONComponent {
	var output []JSONComponent
	// Look for symbols which support nesting
	// A,p Bdir Bdir,p Bind Bind,p Cac Cex E,p P P,p
	// Full list is in Constants "NestedComponentNames"

	position := strings.Index(text, component)

	//removeSymbols(text)

	if position != -1 {
		var currentSymbol JSONComponent
		currentSymbol.Nested = true
		currentSymbol.ComponentType = component

		// Finds first instance of the component
		//fmt.Println("Position is: ", position)

		componentLength := len(component)
		position += componentLength

		text := text[position:]

		//fmt.Println(text)

		// Capture the semantic annotation if any
		if text[0:1] == "[" {
			//fmt.Println("Semantic")

			end := strings.Index((text), "]")

			if end != -1 {
				//fmt.Println("Semantic annotation is: ", text[1:end])
				currentSymbol.SemanticAnnotation = text[1:end]
				text = text[end+1:]

				/*
					brackets := 1

					for i := 0; i < len(text); i++ {
						if text[i] == byte('{') {
							brackets++
						} else if text[i] == byte('}') {
							brackets--
						}
						if brackets == 0 {
							componentContents := text[:i]
							text := text[i+1:]
							fmt.Println("Found end: ", componentContents)
							currentSymbol.Content = componentContents
							fmt.Println("Rest: ", len(text))
							output = append(output, currentSymbol)
							break
						}
					}
					fmt.Println(text)
					return append(output, findNestedPart(text, component)...)
				*/
				// If no closing bracket is found return an empty output
			} else {
				log.Fatalf("Error no end bracket ']' found: " + text)
				return output
			}
		}
		// If the component is nested, get the contents and recurse
		//fmt.Println(text, text[0:1])
		if text[0:1] == "{" {

			fmt.Println("Found nested component: ", text)

			brackets := 1

			componentContents := ""

			for i := 1; i < len(text); i++ {
				if text[i] == byte('{') {
					brackets++
				} else if text[i] == byte('}') {
					brackets--
				}
				if brackets == 0 {
					componentContents = text[1:i]
					text = text[i+1:]
					//fmt.Println("Found end: ", componentContents)
					currentSymbol.Content = removeSymbols(componentContents)
					//fmt.Println("Rest: ", len(text))
					output = append(output, currentSymbol)
					//fmt.Println("Added nested component: ", text)
					break
				}
			}
			//fmt.Println("Appended value", currentSymbol, "\n\n", output)

			// Find any nested components within the nested component
			output = append(output, findNestedPart(componentContents, component)...)
			// Find any further nested components
			output = append(output, findNestedPart(text, component)...)
			//fmt.Println("\n\n RETURNING \n\n", output)
			return output

			// If the component is not a nested component, recurse to look for nested components
		} else {
			//fmt.Println("Not Nested", text)
			return findNestedPart(text, component)
		}
	}

	// If no detections just return the empty output
	return output
}

// Function to remove suffixes (integer id's) from symbols in annotated text
func removeSuffixes(text string) string {
	var regEx *regexp.Regexp

	for i := 0; i < len(RegexStrings); i++ {
		regEx = regexp.MustCompile(RegexStrings[i])
		text = removeSuffixesSymbol(text, regEx, RegexComponents[i])
	}

	return text
}

// Function that removes all suffixes from a single component type in the text
// Takes a text string, the regular expression used, and a component symbol string
// returns the altered text
func removeSuffixesSymbol(text string, regEx *regexp.Regexp, symbol string) string {
	loc := regEx.FindStringIndex(text)

	if loc != nil {
		//fmt.Println(text[loc[0]:loc[1]], text[loc[1]:loc[1]+1], "\n\n")

		if (loc[1] + 1) < len(text) {
			if text[loc[1]:loc[1]+1] == "{" ||
				text[loc[1]:loc[1]+1] == "(" ||
				text[loc[1]:loc[1]+1] == "[" {

				//fmt.Println("Updating text", symbol, text[loc[0]:loc[1]+1])

				//fmt.Println(text, "\n\n")

				text = text[:loc[0]] + symbol + removeSuffixesSymbol(text[loc[1]:], regEx, symbol)

				//fmt.Println(text)
			}
		}

		text = text[:loc[1]] + removeSuffixesSymbol(text[loc[1]:], regEx, symbol)
		//fmt.Println("Found symbol and updated: ", symbol, text)
	}

	return text
}

func getNestedComponents(text string) []JSONComponent {
	var output []JSONComponent

	// Remove suffixes from the input text
	//textPre := text
	text = removeSuffixes(text)
	/*
		if text != textPre {
			fmt.Println("Difference: \n\n", text, "\n\n", textPre)
		}
	*/
	// Get the nested components
	for i := 0; i < len(NestedComponentNames); i++ {
		output = append(output, findNestedPart(text, NestedComponentNames[i])...)
	}

	return output
}

func getNestedComponentsGeneric(text string) ([]JSONComponent, string) {
	var output []JSONComponent

	// Remove suffixes from the input text
	text = removeSuffixes(text)
	//fmt.Println("No suffix text is: ", text)
	// Get the nested components
	var result []JSONComponent
	for i := 0; i < len(NestedComponentNames); i++ {
		// Get the updated text and JSON components
		result, text = findNestedPartGeneric(text, NestedComponentNames[i])
		fmt.Println("Updated text is: ", text)
		// Append the JSON components to the output
		output = append(output, result...)
	}

	return output, text
}

func findNestedPartGeneric(text string, component string) ([]JSONComponent, string) {
	var output []JSONComponent
	var outputText string
	// Look for symbols which support nesting
	// A,p Bdir Bdir,p Bind Bind,p Cac Cex E,p P P,p
	// Full list is in Constants "NestedComponentNames"

	position := strings.Index(text, component)

	if position != -1 {
		var currentSymbol JSONComponent
		currentSymbol.Nested = true
		currentSymbol.ComponentType = component

		componentLength := len(component)
		position += componentLength

		outputText = text[:position]
		text := text[position:]

		//fmt.Println(text)

		// Capture the semantic annotation if any
		if text[0:1] == "[" {
			//fmt.Println("Semantic")

			end := strings.Index((text), "]")

			if end != -1 {
				currentSymbol.SemanticAnnotation = text[1:end]
				outputText += text[:end+1]
				text = text[end+1:]

				// If no closing bracket is found return an empty output
			} else {
				log.Fatalf("Error no end bracket ']' found: " + text)
				return output, text
			}
		}

		// If the component is nested, get the contents and recurse
		if text[0:1] == "{" {

			fmt.Println("Found nested component: ", text)

			brackets := 1

			componentContents := ""

			for i := 1; i < len(text); i++ {
				if text[i] == byte('{') {
					brackets++
				} else if text[i] == byte('}') {
					brackets--
				}
				if brackets == 0 {
					componentContents = text[1:i]
					componentContents = removeSymbols(componentContents)
					if component != "O" {
						outputText += text[:1] + componentContents + text[i:i+1]
					} else {
						outputText += text[:i+1]
					}
					text = text[i+1:]

					//fmt.Println("Found end: ", componentContents)
					currentSymbol.Content = componentContents
					//fmt.Println("Rest: ", len(text))
					output = append(output, currentSymbol)
					//fmt.Println("Added nested component: ", text)
					break
				}
			}

			// Find any further nested components
			result, text := findNestedPartGeneric(text, component)
			output = append(output, result...)
			//fmt.Println("\n\n RETURNING \n\n", output)
			return output, outputText + text

			// If the component is not a nested component, recurse to look for nested components
		} else {
			//fmt.Println("Not Nested", text)
			result, text := findNestedPartGeneric(text, component)
			return result, outputText + text
		}
	}

	// If no detections just return the empty output
	return output, text
}
