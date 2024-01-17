package main

import (
	"fmt"
	"log"
	"strings"
)

// Struct for the ouput file with the components, and a count of each
type Statistics struct {
	Components []JSONComponent
	//
	AttributeCount int
	//
	DirectObjectCount int
	//
	IndirectObjectCount int
	//
	AimCount int
	//
	DeonticCount int
	//
	OrElseCount int
	//
	ActivationConditionCount int
	//
	ExecutionConstraintCount int
}

// Struct for each component with text content, a bool for nesting and semantic annotations
type JSONComponent struct {
	Content            string
	Nested             bool
	SemanticAnnotation string
	ComponentType      string
}

//"Somethignn Cac[afwfawfw]{A(something else) I(Something) Bdir{Nested} Cac(This is another)}", "Cac"
//Somethignn Cac[afwfawfw]{something Cacelse Something Nested his is another}

func main() {
	findNestedPart("Somethignn Cac[afwfawfw]{A(something else) I(Something [AND] something else) Bdir{Nested} Cac(This is another)}", "Cac")
}

func findNestedPart(text string, component string) {

	// Look for symbols which support nesting
	// A,p Bdir Bdir,p Bind Bind,p Cac Cex E,p P P,p

	//
	position := strings.Index(text, component)

	removeSymbols(text)

	if position != -1 {

		// Finds first instance of the component
		fmt.Println("Position is: ", position)

		componentLength := len(component)
		position += componentLength

		text := text[position:]

		fmt.Println(text)

		// Capture the semantic annotation if any
		if text[0:1] == "[" {
			fmt.Println("Semantic")

			end := strings.Index((text), "]")

			if end != -1 {
				fmt.Println("Semantic annotation is: ", text[1:end])
				text := text[end+2:]

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
						fmt.Println("Rest: ", len(text))
						break
					}
				}

				fmt.Println(text)
			} else {
				fmt.Println("Error no end")
			}
		} else if text[0:1] == "{" {
			fmt.Println("Non-semantic")
		} else {
			fmt.Println("Not scoped")
		}

		// After finding scope check for others within the component, and outside of the component
		// Simply recurse until done

		// Capture the contents

		// Add to the output struct
		fmt.Println("done")
	} else {
		fmt.Println("No components found")
	}
}

// Takes a statement in the form of a string, goes through and removes all IG Script notation syntax
func removeSymbols(text string) {

	components := [17]string{ //17
		"A", "A,p", "D", "I", "Bdir", "Bdir,p", "Bind", "Bind,p", "Cac", "Cex", "E", "E,p", "M", "F", "P", "P,p", "O"}

	// Remove all semantic annotations
	//var position int

	for i := 0; i < 17; i++ {
		fmt.Println("Doing component: ", components[i])
		text = removeComponent(text, components[i])
	}

	fmt.Println(text)
	//strings.ReplaceAll(text, "[OR]","or")
	//strings.ReplaceAll(text, "[XOR]","or")
	//strings.ReplaceAll(text, "[AND]","and")
}

// Takes a string and a component, removes all instances of that component from the string
func removeComponent(text string, component string) string {
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

		// If semantic annotation move the position to the end of the annotation
		if text[position] == '[' {
			fmt.Println("Found Semantic annotation")
			position = strings.Index((text), "]") + 1
		}

		// Check if the symbol is a nested symbol
		if text[position:position+1] == "{" {
			fmt.Println("Nested")
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
					fmt.Println("Component contents: ", componentContents)
					break
				}
			}

			if brackets != 0 {
				log.Fatal("Could not find escape bracket, ", text)
				break
			}

			// Replace the component with its contents
			text = text[:start] + componentContents + text[end+1:]
			fmt.Println("Replaced text contents: ", text)
			// Find the next component
			strings.Index(text, component)

			position = strings.Index(text, component)

			// Check if the symbol is a non-nested symbol
		} else if text[position:position+1] == "(" {
			fmt.Println("Not Nested")
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
					fmt.Println("Component contents: ", componentContents)
					break
				}
			}

			if brackets != 0 {
				log.Fatal("Could not find escape bracket, ", text)
				break
			}

			// Replace the component with its contents
			text = text[:start] + componentContents + text[end+1:]
			fmt.Println("Replaced text contents: ", text)
			// Find the next component
			strings.Index(text, component)

			position = strings.Index(text, component)

			// If the symbol is a false positive recurse over the rest of the text until done
		} else {
			// Run the same function for the rest of the text recursively until complete
			text = text[:position+componentLength] + removeComponent(text[position+componentLength:], component)
			return text
		}
	}

	// Return the parsed text with all instances of the symbol removed, maintaining the contents of the symbols
	return text
}
