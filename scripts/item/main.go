package main

import (
	"dbutils/pkg/config"
	"dbutils/pkg/item"
	"dbutils/pkg/utils/errorutil"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
)

var baseItemTypesFile string
var txBaseItemTypesFile string
var tattoosFile string

func init() {
	c := config.LoadConfig("../config.json")
	baseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/baseitemtypes.dat64.json")
	txBaseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/baseitemtypes.dat64.json")

	tattoosFile = filepath.Join(c.ProjectRoot, "assets/tattoos.json")
}

type Tattoo struct {
	En string `json:"en"`
	Zh string `json:"zh"`
}

var enTattooKeyword = "Tattoo"
var zhTattooKeyword = "文身"

func initTattoos(itemTypes []*item.BaseItemType) {

	tattoos := []*Tattoo{}
	for _, itemType := range itemTypes {
		if strings.Contains(itemType.En, enTattooKeyword) && strings.Contains(itemType.Zh, zhTattooKeyword) {
			tattoos = append(tattoos, &Tattoo{
				En: itemType.En,
				Zh: itemType.Zh,
			})
		}
	}

	data, err := json.MarshalIndent(tattoos, "", "  ")
	errorutil.QuitIfError(err)

	os.WriteFile(tattoosFile, data, 0o666)
}

func main() {
	baseItemTypes := item.LoadBaseItemTypesFromGggpk(baseItemTypesFile, txBaseItemTypesFile)
	initTattoos(baseItemTypes)
}
