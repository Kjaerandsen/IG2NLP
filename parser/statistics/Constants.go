package statistics

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
	Name   string `json:"name"`
	BaseTx string `json:"baseTx"`
	Manual string `json:"manual"`
	Stanza string `json:"stanza"`
	//Spacy               string     `json:"stanzaAdvanced"`
	ManualParsed Statistics `json:"manualParsed"`
	StanzaParsed Statistics `json:"stanzaParsed"`
	//SpacyParsed         Statistics `json:"spacyParsed"`
}

// Struct for the ouput file with the components, and a count of each
type StatisticsAuto struct {
	//
	Attributes     []JSONComponent
	AttributeCount int
	//
	AttributeProperties    []JSONComponent
	AttributePropertyCount int
	//
	DirectObjects     []JSONComponent
	DirectObjectCount int
	//
	DirectObjectProperties    []JSONComponent
	DirectObjectPropertyCount int
	//
	IndirectObjects     []JSONComponent
	IndirectObjectCount int
	//
	IndirectObjectProperties    []JSONComponent
	IndirectObjectPropertyCount int
	//
	Aims     []JSONComponent
	AimCount int
	//
	Deontics     []JSONComponent
	DeonticCount int
	//
	OrElses     []JSONComponent
	OrElseCount int
	//
	ActivationConditions     []JSONComponent
	ActivationConditionCount int
	//
	ExecutionConstraints     []JSONComponent
	ExecutionConstraintCount int
	//
	ORCount  int
	XORCount int
	ANDCount int
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

// Struct for each component with text content, a bool for nesting and semantic annotations
type JSONComponentAuto struct {
	Content            string
	Nested             bool
	SemanticAnnotation string
}

type inputStructureAuto []struct {
	Name   string `json:"name"`
	BaseTx string `json:"baseTx"`
	Manual string `json:"manual"`
	Stanza string `json:"stanza"`
	//Spacy               string     `json:"stanzaAdvanced"`
	ManualParsed StatisticsAuto `json:"manualParsed"`
	StanzaParsed StatisticsAuto `json:"stanzaParsed"`
	//SpacyParsed         Statistics `json:"spacyParsed"`
}

type StatisticsCompare struct {
	BaseTx              string `json:"baseTx"`
	Manual              string `json:"mnual"`
	Stanza              string `json:"stanza"`
	BindProperty        int    `json:"BindProperty"`
	IndirectObjectCount int    `json:"IndirectObjectPropertyCount"`
	BdirProperty        int    `json:"BdirProperty"`
	DirectObjectCount   int    `json:"DirectObjectPropertyCount"`
	AProperty           int    `json:"AProperty"`
	AttributeCount      int    `json:"AttributePropertyCount"`
}

type CompareStatistics struct {
	BaseTx                         string          `json:"baseTx"`
	Manual                         string          `json:"manual"`
	Stanza                         string          `json:"stanza"`
	AttributeTP                    int             `json:"attributeTP"`
	AttributePropertyTP            int             `json:"attributePropertyTP"`
	AimTP                          int             `json:"aimTP"`
	DeonticTP                      int             `json:"deonticTP"`
	DirectObjectTP                 int             `json:"directObjectTP"`
	DirectObjectPropertyTP         int             `json:"directObjectPropertyTP"`
	IndirectObjectTP               int             `json:"indirectObjectTP"`
	IndirectObjectPropertyTP       int             `json:"indirectObjectPropertyTP"`
	ActivationConditionTP          int             `json:"activationConditionTP"`
	ExecutionConstraintTP          int             `json:"executionConstraintTP"`
	ConstitutedEntityTP            int             `json:"constitutedEntityTP"`
	ModalTP                        int             `json:"modalTP"`
	ConstitutiveFunctionTP         int             `json:"constitutiveFunctionTP"`
	ConstitutedEntityPropertyTP    int             `json:"constitutedEntityPropertyTP"`
	ConstitutingPropertyTP         int             `json:"constitutingPropertyTP"`
	ConstitutingPropertyPropertyTP int             `json:"constitutingPropertyPropertyTP"`
	OrElseTP                       int             `json:"orElseTP"`
	ExtraComponents                []JSONComponent `json:"extraComponents"`
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
	BaseTx          string              `json:"baseTx"`
	Manual          string              `json:"manual"`
	Stanza          string              `json:"stanza"`
	TP              [17]int             `json:"tp"`
	ExtraComponents [17][]JSONComponent `json:"extraComponents"`
	Count           [20]int             `json:"count"`
}

// Regular expression strings used for removing suffixes (integer identifier for symbols) for statistics
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
