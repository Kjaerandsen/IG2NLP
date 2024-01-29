package statistics

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"

	"IG-Parser/core/parser"
	"IG-Parser/core/tree"
)

// Function to retrieve all symbols from annotated statements
func AutoRunnerGeneric(file string, outFile string) {
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
		var stats StatisticsGeneric

		// Get the statistics from the manually parsed statement
		stats, success := requestHandlerGeneric(data[i].Manual)
		if success {
			data[i].ManualParsed = stats
		}

		// Get the statistics from the automatically parsed statement
		stats, success = requestHandlerGeneric(data[i].Stanza)
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

func requestHandlerGeneric(inputStatement string) (StatisticsGeneric, bool) {
	var output StatisticsGeneric

	// Parse IGScript statement into tree
	stmts, err := parser.ParseStatement(inputStatement)
	if err.ErrorCode != tree.PARSING_NO_ERROR {
		fmt.Println("Error: ", err.ErrorCode)
		fmt.Println("Statement: ", inputStatement)
		return output, false
	}

	statement := stmts[0].Entry.(*tree.Statement)

	// Get all components without nesting
	statementHandlerGeneric(statement, &output)

	// Count occurrences of logical operators
	output.Count[17] = strings.Count(inputStatement, "[OR]")
	output.Count[18] = strings.Count(inputStatement, "[XOR]")
	output.Count[19] = strings.Count(inputStatement, "[AND]")

	// Get all components with nesting
	nestedComponents := getNestedComponents(inputStatement)

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

	return output, true
}

// Handler for statements, takes a statement and the statistics struct,
// gets the stats for each component in the statement and enters them into the statistics struct
func statementHandlerGeneric(statement *tree.Statement, stats *StatisticsGeneric) {

	// Regulative
	getComponentInfoGeneric(statement.Attributes, "A", stats)
	getComponentInfoGeneric(statement.Deontic, "D", stats)
	getComponentInfoGeneric(statement.DirectObject, "Bdir", stats)
	getComponentInfoGeneric(statement.DirectObjectComplex, "Bdir", stats)
	getComponentInfoGeneric(statement.IndirectObject, "Bind", stats)
	getComponentInfoGeneric(statement.IndirectObjectComplex, "Bind", stats)
	getComponentInfoGeneric(statement.Aim, "I", stats)
	// Regulative Properties
	getComponentInfoGeneric(statement.AttributesPropertySimple, "A,p", stats)
	getComponentInfoGeneric(statement.AttributesPropertyComplex, "A,p", stats)
	getComponentInfoGeneric(statement.DirectObjectPropertySimple, "Bdir,p", stats)
	getComponentInfoGeneric(statement.DirectObjectPropertyComplex, "Bdir,p", stats)
	getComponentInfoGeneric(statement.IndirectObjectPropertySimple, "Bind,p", stats)
	getComponentInfoGeneric(statement.IndirectObjectPropertyComplex, "Bind,p", stats)
	// Constitutive
	getComponentInfoGeneric(statement.ConstitutedEntity, "E", stats)
	getComponentInfoGeneric(statement.Modal, "M", stats)
	getComponentInfoGeneric(statement.ConstitutiveFunction, "F", stats)
	getComponentInfoGeneric(statement.ConstitutingProperties, "P", stats)
	getComponentInfoGeneric(statement.ConstitutingPropertiesComplex, "P", stats)
	// Constitutive Properties
	getComponentInfoGeneric(statement.ConstitutedEntityPropertySimple, "E,p", stats)
	getComponentInfoGeneric(statement.ConstitutedEntityPropertyComplex, "E,p", stats)
	getComponentInfoGeneric(statement.ConstitutingPropertiesPropertySimple, "P,p", stats)
	getComponentInfoGeneric(statement.ConstitutingPropertiesPropertyComplex, "P,p", stats)
	// Shared
	getComponentInfoGeneric(statement.ActivationConditionComplex, "Cac", stats)
	getComponentInfoGeneric(statement.ActivationConditionSimple, "Cac", stats)
	getComponentInfoGeneric(statement.ExecutionConstraintComplex, "Cex", stats)
	getComponentInfoGeneric(statement.ExecutionConstraintSimple, "Cex", stats)
	getComponentInfoGeneric(statement.OrElse, "O", stats)
}

// Recursive function which goes over a symbol and it's children, adding the components to the statistics struct
func getComponentInfoGeneric(componentNode *tree.Node, symbol string, stats *StatisticsGeneric) {
	var component JSONComponent
	component.SemanticAnnotation = ""
	component.Nested = false

	// If the component is invalid exit
	if componentNode == nil {
		//fmt.Println("Node is not initialized\n")
		return
	}
	//fmt.Println("Lets go")

	if reflect.TypeOf(componentNode.Entry) == nil {
		//fmt.Println("Symbol: ", symbol)
		//fmt.Println(componentNode.LogicalOperator)
		getComponentInfoGeneric(componentNode.Left, symbol, stats)
		getComponentInfoGeneric(componentNode.Right, symbol, stats)
	} else {
		// If the statement is nested set the nested variable to true and handle the nested components
		if statement, ok := componentNode.Entry.(*tree.Statement); ok {
			statementHandlerGeneric(statement, stats)
			component.Nested = true
		}

		// Set the text content and semantic annotation of the component
		component.Content = fmt.Sprintf("%v", componentNode.Entry)
		component.SemanticAnnotation = fmt.Sprintf("%v", componentNode.Annotations)

		// Remove empty semantic annotations
		if component.SemanticAnnotation == "\u003cnil\u003e" {
			component.SemanticAnnotation = ""
		}

		component.ComponentType = symbol

		// Only add non-nested symbols
		// Nested symbols are handled separately
		if !component.Nested {
			for j := 0; j < len(ComponentNames); j++ {
				if symbol == ComponentNames[j] {
					stats.Components[j] = append(stats.Components[j], component)
					stats.Count[j]++
				}
			}
		}
	}
}
