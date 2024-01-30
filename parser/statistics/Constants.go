package statistics

// Struct for each component with text content, a bool for nesting and semantic annotations
type JSONComponent struct {
	Content            string
	Nested             bool
	SemanticAnnotation string
	ComponentType      string
	StartID            int
}

type Component int

const (
	Ap Component = iota
	Bdir
	Bdirp
	Bind
	Bindp
	Cac
	Cex
	Ep
	P
	Pp
	O
	A
	D
	I
	E
	M
	F
)

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
	PartialPool     []PartialPool          `json:"partialPool"`
	// For partial matches of the same type
	PartialCount [17]int
	// Count 1 is Manual, 2 is Stanza
	// Count 1 is false negative, Count 2 is false positive
	Count [2][20]int `json:"count"`
}

type CompareOut struct {
	BaseTx string `json:"baseTx"`
	Manual string `json:"manual"`
	Stanza string `json:"stanza"`
	// Components which are not true positive matches
	ExtraComponents [2][]JSONComponent `json:"extraComponents"`
	PartialPool     []PartialPool      `json:"partialPool"`
	// Count
	Count StatisticsCount `json:"count"`
}

// Count for statistics of the properties, TP, PP, FP, FN
// True positive, partial positive, false positive and false negative
type StatisticsCount struct {
	AttributeProperty                [4]int `json:"AttributeProperty"`
	DirectObject                     [4]int `json:"DirectObject"`
	DirectObjectProperty             [4]int `json:"DirectObjectProperty"`
	IndirectObject                   [4]int `json:"IndirectObject"`
	IndirectObjectProperty           [4]int `json:"IndirectObjectProperty"`
	ActivationCondition              [4]int `json:"ActivationCondition"`
	ExecutionConstraint              [4]int `json:"ExecutionConstraint"`
	ConstitutedEntityProperty        [4]int `json:"ConstitutedEntityProperty"`
	ConstitutingProperties           [4]int `json:"ConstitutingProperties"`
	ConstitutingPropertiesProperties [4]int `json:"ConstitutingPropertiesProperties"`
	OrElse                           [4]int `json:"OrElse"`
	Attribute                        [4]int `json:"Attribute"`
	Deontic                          [4]int `json:"Deontic"`
	Aim                              [4]int `json:"Aim"`
	ConstitutedEntity                [4]int `json:"ConstitutedEntity"`
	Modal                            [4]int `json:"Modal"`
	ConstitutiveFunction             [4]int `json:"ConstitutiveFunction"`
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

type PartialPool struct {
	ManualComponents []JSONComponent
	StanzaComponents []JSONComponent
}
