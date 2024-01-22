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
	"A", "A,p", "D", "I", "Bdir", "Bdir,p", "Bind", "Bind,p",
	"Cac", "Cex", "E", "E,p", "M", "F", "P", "P,p", "O"}

type inputStructure []struct {
	Name          string `json:"name"`
	BaseText      string `json:"baseText"`
	ProcessedText string `json:"processedText"`
	Stanza        string `json:"stanza"`
	//Spacy               string     `json:"stanzaAdvanced"`
	ProcessedTextParsed Statistics `json:"processedTextParsed"`
	StanzaParsed        Statistics `json:"stanzaParsed"`
	//SpacyParsed         Statistics `json:"spacyParsed"`
}

// Struct for the ouput file with the components, and a count of each
type StatisticsAuto struct {
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
	//
	ActivationConditions     []JSONComponent
	ActivationConditionCount int
	//
	ExecutionConstraints     []JSONComponent
	ExecutionConstraintCount int
}

// Struct for each component with text content, a bool for nesting and semantic annotations
type JSONComponentAuto struct {
	Content            string
	Nested             bool
	SemanticAnnotation string
}

type inputStructureAuto []struct {
	Name          string `json:"name"`
	BaseText      string `json:"baseText"`
	ProcessedText string `json:"processedText"`
	Stanza        string `json:"stanza"`
	//Spacy               string     `json:"stanzaAdvanced"`
	ProcessedTextParsed StatisticsAuto `json:"processedTextParsed"`
	StanzaParsed        StatisticsAuto `json:"stanzaParsed"`
	//SpacyParsed         Statistics `json:"spacyParsed"`
}

type StatisticsCompare struct {
	BaseText            string `json:"baseText"`
	ProcessedText       string `json:"processedText"`
	Stanza              string `json:"stanza"`
	BindProperty        int    `json:"BindProperty"`
	IndirectObjectCount int    `json:"IndirectObjectPropertyCount"`
	BdirProperty        int    `json:"BdirProperty"`
	DirectObjectCount   int    `json:"DirectObjectPropertyCount"`
	AProperty           int    `json:"AProperty"`
	AttributeCount      int    `json:"AttributePropertyCount"`
}

// Regular expression strings used for removing suffixes (integer identifier for symbols) for statistics
var RegexStrings = []string{
	"A\\d*",
	"A\\d*,p\\d*",
	"D\\d*",
	"I\\d*",
	"Bdir\\d*",
	"Bdir\\d*,p\\d*",
	"Bind\\d*",
	"Bind\\d*,p\\d*",
	"Cac\\d*",
	"Cex\\d*",
	"E\\d*",
	"E,pd*\\d*",
	"M\\d*",
	"F\\d*",
	"P\\d*",
	"P\\*d,p\\d*",
	"O\\d*",
}
