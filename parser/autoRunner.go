package main

import (
	"IG-Parser/core/parser"
	"IG-Parser/core/tree"
	"encoding/json"
	"fmt"
	"os"
	"reflect"
)

type Statistics struct {
	//
	Attributes     []JSONComponent
	AttributeCount int
	//
	DirectObjects     []JSONComponent
	DirectObjectCount int
	//
	IndirectObjects     []JSONComponent
	IndirectObjectCount int
	//
	Aims     []JSONComponent
	AimCount int
	//
	Deontics     []JSONComponent
	DeonticCount int
	//
	OrElses     []JSONComponent
	OrElseCount int
}

type JSONComponent struct {
	Content            string
	Nested             bool
	SemanticAnnotation string
}

type inputStructure []struct {
	Name                string     `json:"name"`
	BaseText            string     `json:"baseText"`
	ProcessedText       string     `json:"processedText"`
	Stanza              string     `json:"stanza"`
	Spacy               string     `json:"stanzaAdvanced"`
	ProcessedTextParsed Statistics `json:"processedTextParsed"`
	StanzaParsed        Statistics `json:"stanzaParsed"`
	SpacyParsed         Statistics `json:"spacyParsed"`
}

func main() {
	// Read the input file
	file := "./input.json"

	content, err := os.ReadFile(file)
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

	for i := 0; i < len(data); i++ {
		var stats Statistics

		stats, success := requestHandler(data[i].ProcessedText)
		if success {
			data[i].ProcessedTextParsed = stats
		}

		stats, success = requestHandler(data[i].Spacy)
		if success {
			data[i].SpacyParsed = stats
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
	err = os.WriteFile(file, jsonData, 0644)
	if err != nil {
		fmt.Println("Error writing to file:", err)
		return
	}

	//http.HandleFunc("/statement", requestHandler)

}

func requestHandler(inputStatement string) (Statistics, bool) {
	var output Statistics

	// Parse IGScript statement into tree
	stmts, err := parser.ParseStatement(inputStatement)
	if err.ErrorCode != tree.PARSING_NO_ERROR {
		fmt.Println("Error: ", err.ErrorCode)
		fmt.Println("Statement: ", inputStatement)
		return output, false
	}

	statement := stmts[0].Entry.(*tree.Statement)

	statementHandler(statement, &output)

	return output, true
}

// Handler for statements, takes a statement and the statistics struct,
// gets the stats for each component in the statement and enters them into the statistics struct
func statementHandler(statement *tree.Statement, stats *Statistics) {

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
func getComponentInfo(componentNode *tree.Node, symbol string, stats *Statistics) {
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
			//fmt.Println("statement is: ", statement)
			statementHandler(statement, stats)
			component.Nested = true
			component.Content = fmt.Sprintf("%v", componentNode.Entry)
			component.SemanticAnnotation = fmt.Sprintf("%v", componentNode.Annotations)
		} else {
			component.Nested = false
			component.Content = fmt.Sprintf("%v", componentNode.Entry)
			component.SemanticAnnotation = fmt.Sprintf("%v", componentNode.Annotations)
			//fmt.Println(componentNode.Entry)
			//fmt.Println(reflect.TypeOf(componentNode.Entry))
		}
		switch symbol {
		case "A":
			stats.AttributeCount += 1
			stats.Attributes = append(stats.Attributes, component)
		case "D":
			stats.DeonticCount += 1
			stats.Deontics = append(stats.Deontics, component)
		case "Bdir":
			stats.DirectObjectCount += 1
			stats.DirectObjects = append(stats.DirectObjects, component)
		case "Bind":
			stats.IndirectObjectCount += 1
			stats.IndirectObjects = append(stats.IndirectObjects, component)
		case "Cac":
			//stats. += 1
			//stats.Deontics = append(stats.Deontics, component)
		case "I":
			stats.AimCount += 1
			stats.Aims = append(stats.Aims, component)
		}
	}

	//fmt.Print("\n")
}
