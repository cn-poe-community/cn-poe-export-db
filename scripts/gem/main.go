package main

import (
	"dbutils/pkg/config"
	"dbutils/pkg/gem"
	"dbutils/pkg/item"
	"dbutils/pkg/utils/errorutil"
	"dbutils/pkg/utils/stringutil"
	"encoding/json"
	"os"
	"path/filepath"
)

var baseItemTypesFile string
var txBaseItemTypesFile string
var gemEffectsFile string
var txGemEffectsFile string

var gemsFile string

func init() {
	c := config.LoadConfig("../config.json")
	baseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/baseitemtypes.dat64.json")
	txBaseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/baseitemtypes.dat64.json")
	gemEffectsFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/gemeffects.dat64.json")
	txGemEffectsFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/gemeffects.dat64.json")

	gemsFile = filepath.Join(c.ProjectRoot, "assets/gems/gems.json")
}

func initGems(baseTypes []*item.BaseItemType, gemEffects []*gem.GemEffect) {
	gems := []*gem.Gem{}
	for _, baseType := range baseTypes {
		if !stringutil.IsASCII(baseType.Zh) &&
			(baseType.GgpkType.ItemClassesKey == 18 ||
				baseType.GgpkType.ItemClassesKey == 19) {
			gems = append(gems, &gem.Gem{
				En: baseType.En,
				Zh: baseType.Zh,
			})
		}
	}

	gemMap := map[string]*gem.Gem{}
	for _, gem := range gems {
		gemMap[gem.Zh] = gem
	}

	transfiguredGems := []*gem.Gem{}
	transfiguredGemMap := map[string]*gem.Gem{}
	for _, effect := range gemEffects {
		zh := effect.Zh
		if !stringutil.IsASCII(zh) {
			if _, ok := gemMap[zh]; !ok {
				if _, ok := transfiguredGemMap[zh]; !ok {
					g := &gem.Gem{
						En: effect.En,
						Zh: effect.Zh,
					}
					transfiguredGems = append(transfiguredGems, g)
					transfiguredGemMap[g.Zh] = g
				}
			}
		}
	}

	gems = append(gems, transfiguredGems...)

	data, err := json.MarshalIndent(gems, "", "  ")
	errorutil.QuitIfError(err)

	os.WriteFile(gemsFile, data, 0o666)
}

func main() {
	baseItemTypes := item.LoadBaseItemTypesFromGggpk(baseItemTypesFile, txBaseItemTypesFile)
	gemEffects := gem.LoadGemEffectsFromGgpk(gemEffectsFile, txGemEffectsFile)
	initGems(baseItemTypes, gemEffects)
}
