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

func AutoRunner(file string, outFile string) {
	// Read the input file

	content, err := os.ReadFile(file)
	if err != nil {
		fmt.Println("Error reading file:", err)
		return
	}

	var data inputStructureAuto

	err = json.Unmarshal(content, &data)
	if err != nil {
		fmt.Println("Error unmarshalling JSON:", err)
		return
	}

	fmt.Println(len(data))

	for i := 0; i < len(data); i++ {
		var stats StatisticsAuto

		stats, success := requestHandler(data[i].Manual)
		if success {
			data[i].ManualParsed = stats
		}

		stats, success = requestHandler(data[i].Stanza)
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

		stats, success := requestHandlerGeneric(data[i].Manual)
		if success {
			data[i].ManualParsed = stats
		}

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

	fmt.Println("Getting nested components from \n", inputStatement)

	nestedComponents := getNestedComponents(inputStatement)

	// Go through all components detected

	//fmt.Println("Nested Components: ")
	//fmt.Println(nestedComponents, len(nestedComponents))

	for i := 0; i < len(nestedComponents); i++ {
		// If the type is within the ComponentNames
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

func requestHandler(inputStatement string) (StatisticsAuto, bool) {
	var output StatisticsAuto

	// Parse IGScript statement into tree
	stmts, err := parser.ParseStatement(inputStatement)
	if err.ErrorCode != tree.PARSING_NO_ERROR {
		fmt.Println("Error: ", err.ErrorCode)
		fmt.Println("Statement: ", inputStatement)
		return output, false
	}

	statement := stmts[0].Entry.(*tree.Statement)

	// Get all components without nesting
	statementHandler(statement, &output)
	// Count occurrences of logical operators
	output.ORCount = strings.Count(inputStatement, "[OR]")
	output.XORCount = strings.Count(inputStatement, "[XOR]")
	output.ANDCount = strings.Count(inputStatement, "[AND]")
	// Get all components with nesting
	nestedComponents := getNestedComponents(inputStatement)

	for i := 0; i < len(nestedComponents); i++ {
		switch nestedComponents[i].ComponentType {
		case "A,p":
			output.AttributeProperties = append(output.AttributeProperties, nestedComponents[i])
			output.AttributeCount += 1
		case "Bdir":
			output.DirectObjects = append(output.DirectObjects, nestedComponents[i])
			output.DirectObjectCount += 1
		case "Bdir,p":
			output.DirectObjectProperties = append(output.DirectObjectProperties, nestedComponents[i])
			output.DirectObjectPropertyCount += 1
		case "Bind":
			output.IndirectObjects = append(output.IndirectObjects, nestedComponents[i])
			output.IndirectObjectCount += 1
		case "Bind,p":
			output.IndirectObjectProperties = append(output.IndirectObjectProperties, nestedComponents[i])
			output.IndirectObjectPropertyCount += 1
		case "Cac":
			output.ActivationConditions = append(output.ActivationConditions, nestedComponents[i])
			output.ActivationConditionCount += 1
		case "Cex":
			output.ExecutionConstraints = append(output.ExecutionConstraints, nestedComponents[i])
			output.ExecutionConstraintCount += 1
		case "E,p":
			fmt.Println("E,p")
		case "P":
			fmt.Println("P")
		case "P,p":
			fmt.Println("P,p")
		case "O":
			output.OrElses = append(output.OrElses, nestedComponents[i])
			output.OrElseCount += 1
		}
	}

	return output, true
}

// Handler for statements, takes a statement and the statistics struct,
// gets the stats for each component in the statement and enters them into the statistics struct
func statementHandler(statement *tree.Statement, stats *StatisticsAuto) {

	// Regulative
	getComponentInfo(statement.Attributes, "A", stats)
	getComponentInfo(statement.Deontic, "D", stats)
	getComponentInfo(statement.DirectObject, "Bdir", stats)
	getComponentInfo(statement.DirectObjectComplex, "Bdir", stats)
	getComponentInfo(statement.IndirectObject, "Bind", stats)
	getComponentInfo(statement.IndirectObjectComplex, "Bind", stats)
	getComponentInfo(statement.Aim, "I", stats)
	// Regulative Properties
	getComponentInfo(statement.AttributesPropertySimple, "A,p", stats)
	getComponentInfo(statement.AttributesPropertyComplex, "A,p", stats)
	getComponentInfo(statement.DirectObjectPropertySimple, "Bdir,p", stats)
	getComponentInfo(statement.DirectObjectPropertyComplex, "Bdir,p", stats)
	getComponentInfo(statement.IndirectObjectPropertySimple, "Bind,p", stats)
	getComponentInfo(statement.IndirectObjectPropertyComplex, "Bind,p", stats)
	// Constitutive
	getComponentInfo(statement.ConstitutedEntity, "E", stats)
	getComponentInfo(statement.Modal, "M", stats)
	getComponentInfo(statement.ConstitutiveFunction, "F", stats)
	getComponentInfo(statement.ConstitutingProperties, "P", stats)
	getComponentInfo(statement.ConstitutingPropertiesComplex, "P", stats)
	// Constitutive Properties
	getComponentInfo(statement.ConstitutedEntityPropertySimple, "E,p", stats)
	getComponentInfo(statement.ConstitutedEntityPropertyComplex, "E,p", stats)
	getComponentInfo(statement.ConstitutingPropertiesPropertySimple, "P,p", stats)
	getComponentInfo(statement.ConstitutingPropertiesPropertyComplex, "P,p", stats)

	// Shared
	getComponentInfo(statement.ActivationConditionComplex, "Cac", stats)
	getComponentInfo(statement.ActivationConditionSimple, "Cac", stats)
	getComponentInfo(statement.ExecutionConstraintComplex, "Cex", stats)
	getComponentInfo(statement.ExecutionConstraintSimple, "Cex", stats)
	getComponentInfo(statement.OrElse, "O", stats)
}

// Recursive function which goes over a symbol and it's children, adding the components to the statistics struct
func getComponentInfo(componentNode *tree.Node, symbol string, stats *StatisticsAuto) {
	var component JSONComponent
	component.SemanticAnnotation = ""

	//var componentInfo JSONComponent
	//fmt.Println("Symbol: ", symbol)
	if componentNode == nil {
		//fmt.Println("Node is not initialized\n")
		return
	}
	//fmt.Println("Lets go")

	if reflect.TypeOf(componentNode.Entry) == nil {
		//fmt.Println("Symbol: ", symbol)
		//fmt.Println(componentNode.LogicalOperator)

		getComponentInfo(componentNode.Left, symbol, stats)
		getComponentInfo(componentNode.Right, symbol, stats)
	} else {
		if statement, ok := componentNode.Entry.(*tree.Statement); ok {
			// StringFlat gives the string
			fmt.Println("statement is: ", componentNode.StringFlat())
			fmt.Println(componentNode)
			statementHandler(statement, stats)

			//fmt.Println("No looking at stuff\n")
			//fmt.Println(componentNode.Entry.(*tree.Statement).String())

			// Statement in this case includes all subcomponents and their contents
			// Need to go through each, get the text, and output it
			//fmt.Println(stats)
			//fmt.Println(componentNode.Entry)

			component.Nested = true
		} else {
			component.Nested = false
			//fmt.Println(componentNode.Entry)
			//fmt.Println(reflect.TypeOf(componentNode.Entry))
		}

		component.Content = fmt.Sprintf("%v", componentNode.Entry)
		component.SemanticAnnotation = fmt.Sprintf("%v", componentNode.Annotations)

		// Remove empty semantic annotations
		if component.SemanticAnnotation == "\u003cnil\u003e" {
			component.SemanticAnnotation = ""
		}

		// Only add non-nested symbols
		// Nested symbols are handled separately
		if !component.Nested {
			switch symbol {
			case "A":
				stats.AttributeCount += 1
				stats.Attributes = append(stats.Attributes, component)
			case "A,p":
				stats.AttributePropertyCount += 1
				stats.AttributeProperties = append(stats.AttributeProperties, component)
			case "D":
				stats.DeonticCount += 1
				stats.Deontics = append(stats.Deontics, component)
			case "Bdir":
				stats.DirectObjectCount += 1
				stats.DirectObjects = append(stats.DirectObjects, component)
			case "Bdir,p":
				stats.DirectObjectPropertyCount += 1
				stats.DirectObjectProperties = append(stats.DirectObjectProperties, component)
			case "Bind":
				stats.IndirectObjectCount += 1
				stats.IndirectObjects = append(stats.IndirectObjects, component)
			case "Bind,p":
				stats.IndirectObjectPropertyCount += 1
				stats.IndirectObjectProperties = append(stats.IndirectObjectProperties, component)
			case "Cac":
				stats.ActivationConditionCount += 1
				stats.ActivationConditions = append(stats.ActivationConditions, component)
			case "Cex":
				stats.ExecutionConstraintCount += 1
				stats.ExecutionConstraints = append(stats.ExecutionConstraints, component)
			case "I":
				stats.AimCount += 1
				stats.Aims = append(stats.Aims, component)
			}
		}
	}

	//fmt.Print("\n")
}

// Recursive function which goes over a symbol and it's children, adding the components to the statistics struct
func getComponentInfoGeneric(componentNode *tree.Node, symbol string, stats *StatisticsGeneric) {
	var component JSONComponent
	component.SemanticAnnotation = ""

	//var componentInfo JSONComponent
	//fmt.Println("Symbol: ", symbol)
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
		if statement, ok := componentNode.Entry.(*tree.Statement); ok {
			// StringFlat gives the string
			//fmt.Println("statement is: ", componentNode.StringFlat())
			//fmt.Println(componentNode)
			statementHandlerGeneric(statement, stats)

			//fmt.Println("No looking at stuff\n")
			//fmt.Println(componentNode.Entry.(*tree.Statement).String())

			// Statement in this case includes all subcomponents and their contents
			// Need to go through each, get the text, and output it
			//fmt.Println(stats)
			//fmt.Println(componentNode.Entry)

			component.Nested = true
		} else {
			component.Nested = false
			//fmt.Println(componentNode.Entry)
			//fmt.Println(reflect.TypeOf(componentNode.Entry))
		}

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
