package statistics

// Struct for each component with text content, a bool for nesting and semantic annotations
type JSONComponent struct {
	Content            string
	Nested             bool
	SemanticAnnotation string
	ComponentType      string
	StartID            int
}

var ComponentNames = [17]string{ //17
	// First line is components with nesting (11)
	"A,p", "Bdir", "Bdir,p", "Bind", "Bind,p", "Cac", "Cex", "E,p", "P", "P,p", "O",
	// Second line is without support for nesting
	"A", "D", "I", "E", "M", "F"}

var NestedComponentNames = [11]string{
	"A,p", "Bdir", "Bdir,p", "Bind", "Bind,p",
	"Cac", "Cex", "E,p", "P", "P,p", "O"}

type inputStructure []struct {
	Name         string     `json:"name"`
	BaseTx       string     `json:"baseTx"`
	Manual       string     `json:"manual"`
	Stanza       string     `json:"stanza"`
	ManualParsed Statistics `json:"manualParsed"`
	StanzaParsed Statistics `json:"stanzaParsed"`
}

type textComparison struct {
	Name             string   `json:"name"`
	BaseTx           string   `json:"baseTx"`
	Manual           string   `json:"manual"`
	Stanza           string   `json:"stanza"`
	ManualReversed   string   `json:"manualReversed"`
	StanzaReversed   string   `json:"stanzaReversed"`
	StanzaDifference []string `json:"stanzaDifference"`
	ManualDifference []string `json:"manualDifference"`
}

type inputStructureGeneric []struct {
	Name         string            `json:"name"`
	BaseTx       string            `json:"baseTx"`
	Manual       string            `json:"manual"`
	Stanza       string            `json:"stanza"`
	ManualParsed StatisticsGeneric `json:"manualParsed"`
	StanzaParsed StatisticsGeneric `json:"stanzaParsed"`
}

type StatisticsGeneric struct {
	Components [17][]JSONComponent `json:"components"`
	Count      [20]int             `json:"count"`
}

type CompareStatisticsGeneric struct {
	BaseTx string `json:"baseTx"`
	Manual string `json:"manual"`
	Stanza string `json:"stanza"`
	// Amount of true positive matches
	TP [17]int `json:"tp"`
	// Components which are not true positive matches
	ExtraComponents [2][17][]JSONComponent `json:"extraComponents"`
	Count           [2][20]int             `json:"count"`
}

// Regular expression strings used for removing suffixes (integer identifier for symbols) for statistics
// Ordered to first remove suffixes preceeding properties, then property suffixes if present
var RegexStrings = [12]string{
	"A\\d*",
	"A,p\\d*",
	"I\\d*",
	"Bdir\\d*",
	"Bdir,p\\d*",
	"Bind\\d*",
	"Bind,p\\d*",
	"Cex\\d*",
	"E\\d*",
	"E,p\\d*",
	"P\\d*",
	"P,p\\d*",
}

// RegexComponents used to remove suffixes from components
var RegexComponents = [12]string{
	"A",
	"A,p",
	"I",
	"Bdir",
	"Bdir,p",
	"Bind",
	"Bind,p",
	"Cex",
	"E",
	"E,p",
	"P",
	"P,p",
}

// Struct for the ouput file with the components, and a count of each
type Statistics struct {
	Components []JSONComponent
	//
	AttributeCount         int
	AttributePropertyCount int
	//
	DirectObjectCount         int
	DirectObjectPropertyCount int
	//
	IndirectObjectCount         int
	IndirectObjectPropertyCount int
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
	//
	ConstitutedEntityCount         int
	ConstitutedEntityPropertyCount int
	//
	ModalCount int
	//
	ConstitutiveFunctionCount int
	//
	ConstitutingPropertiesCount         int
	ConstitutingPropertiesPropertyCount int
	//
	ORCount  int
	XORCount int
	ANDCount int
}
