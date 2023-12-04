package main

import (
	"dbutils/pkg/config"
	"dbutils/pkg/gem"
	"dbutils/pkg/item"
	"dbutils/pkg/utils/errorutil"
	"encoding/json"
	"os"
	"path/filepath"
)

var baseItemTypesFile string
var txBaseItemTypesFile string

var gemsFile string

func init() {
	c := config.LoadConfig("../config.json")
	baseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/baseitemtypes.dat64.json")
	txBaseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/baseitemtypes.dat64.json")

	gemsFile = filepath.Join(c.ProjectRoot, "assets/gems/gems.json")
}

func initGems(baseTypes []*item.BaseItemType) {
	gems := []*gem.Gem{}
	for _, baseType := range baseTypes {
		if baseType.GgpkType.ItemClassesKey == 18 || baseType.GgpkType.ItemClassesKey == 19 {
			gems = append(gems, &gem.Gem{
				En: baseType.En,
				Zh: baseType.Zh,
			})
		}
	}

	data, err := json.MarshalIndent(gems, "", "  ")
	errorutil.QuitIfError(err)

	os.WriteFile(gemsFile, data, 0o666)
}

func main() {
	baseItemTypes := item.LoadBaseItemTypesFromGggpk(baseItemTypesFile, txBaseItemTypesFile)
	initGems(baseItemTypes)
}
