package main

import (
	"IG-Parser/core/parser"
	"IG-Parser/core/tree"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
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

type inputData struct {
	Statement string `json:"statement"`
}

func main() {
	http.HandleFunc("/statement", requestHandler)

	// Start the HTTP server
	port := 3001
	fmt.Printf("Server listening on :%d...\n", port)
	err := http.ListenAndServe(fmt.Sprintf(":%d", port), nil)
	if err != nil {
		log.Fatal("Web service stopped. Error:", err)
	}
}

func requestHandler(w http.ResponseWriter, r *http.Request) {
	//input := "Cac{Once E(policy) F(comes into force)} A,p(relevant) A(regulators) D(must) I(monitor [AND] enforce) Bdir(compliance)."
	requestBody, err1 := io.ReadAll(r.Body)
	if err1 != nil {
		http.Error(w, "Error reading request body", http.StatusInternalServerError)
		return
	}

	// Parse JSON request body
	var input inputData
	err1 = json.Unmarshal(requestBody, &input)
	if err1 != nil {
		http.Error(w, `Bad JSON input, send body in the format {"statement":"parsed statement here"}`, http.StatusBadRequest)
		return
	}

	var output Statistics

	fmt.Println("input statement is: ", input.Statement)

	// Parse IGScript statement into tree
	stmts, err := parser.ParseStatement(input.Statement)
	if err.ErrorCode != tree.PARSING_NO_ERROR {
		fmt.Println("Error: ", err.ErrorCode)
		return
	}

	//fmt.Println(reflect.TypeOf(stmts))

	statement := stmts[0].Entry.(*tree.Statement)

	statementHandler(statement, &output)

	//fmt.Println(output)

	outputJSON, err1 := json.Marshal(output)
	if err1 != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	// Set response headers
	w.Header().Set("Content-Type", "application/json")

	// Write JSON response
	w.WriteHeader(http.StatusOK)
	w.Write(outputJSON)

	fmt.Println("Handled request")
	/*
		one, two := endpoints.ConvertIGScriptToTabularOutput(input, "1", tabular.OUTPUT_TYPE_NONE, "", true, true)

		fmt.Println(one)
		fmt.Println(two)
	*/
	/*
		statement, err := endpoints.ConvertIGScriptToVisualTree(input, "1", "")
		if err.ErrorCode == tree.PARSING_NO_ERROR {
			fmt.Println(statement)
		} else {
			fmt.Println("Error: ", err.ErrorCode)
		}
	*/
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
