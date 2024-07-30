package main

import (
	"dbutils/pkg/config"
	"dbutils/pkg/gem"
	"dbutils/pkg/item"
	"dbutils/pkg/trade"
	"dbutils/pkg/utils/errorutil"
	"dbutils/pkg/utils/stringutil"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
)

var baseItemTypesFile string
var gemEffectsFile string

var txBaseItemTypesFile string
var txGemEffectsFile string

var gemsFile string

var tradableItemsFile string

// 已经移除的无效宝石，通过将basetypes中的数据与indexables中的数据进行diff得到，并通过了人工检查
// 后续由人工维护
var removedGemList = []string{"Righteous Lightning", "Wildfire", "Playtest Spell", "Infernal Sweep",
	"New Blade Vortex", "Capture Monster", "Ignite", "Wand Teleport", "Lightning Channel",
	"Lesser Reduced Mana Cost Support", "Static Tether", "Shadow Blades", "Backstab", "New Shock Nova",
	"Rending Steel", "Quickstep", "Ancestral Blademaster", "Fire Weapon", "Item Quantity Support", "Icefire",
	"NewPunishment", "Playtest Attack", "Vortex Mine", "Discorectangle Slam", "Elemental Projectiles",
	"Lightning Circle", "Split Projectiles Support", "Damage Infusion", "Blinding Aura", "Gluttony of Elements",
	"Summon Skeletons Channelled", "Spectral Spinning Weapon", "Riptide", "Flammable Shot",
}

var removedGemSet = map[string]bool{}

func init() {
	c := config.LoadConfig("../config.json")
	baseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/baseitemtypes.dat64.json")
	gemEffectsFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/gemeffects.dat64.json")

	txBaseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/baseitemtypes.dat64.json")
	txGemEffectsFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/gemeffects.dat64.json")

	gemsFile = filepath.Join(c.ProjectRoot, "assets/gems/gems.json")

	tradableItemsFile = filepath.Join(c.ProjectRoot, "docs/trade/tx/items")

	for _, en := range removedGemList {
		removedGemSet[en] = true
	}
}

func loadGemsFromTradableItemsData() []map[string]any {
	itemData, err := trade.LoadItemData(tradableItemsFile)
	errorutil.QuitIfError(err)

	for _, resultEntry := range itemData.Result {
		if resultEntry.Id == "gems" {
			return resultEntry.Entries
		}
	}

	log.Fatal("load tradable gems failed")
	return nil
}

func initGems(baseTypes []*item.BaseItemType, gemEffects []*gem.GemEffect, tradableGems []map[string]any) {

	gems := []*gem.Gem{}
	for _, baseType := range baseTypes {
		if !stringutil.IsASCII(baseType.Zh) &&
			(baseType.GgpkType.ItemClassesKey == 18 ||
				baseType.GgpkType.ItemClassesKey == 19) {
			gems = append(gems, &gem.Gem{
				En: baseType.En,
				Zh: formatGemZh(baseType.Zh),
			})
		}
	}

	gemZhIdx := map[string]*gem.Gem{}
	for _, gem := range gems {
		gemZhIdx[gem.Zh] = gem
	}

	transfiguredGems := []*gem.Gem{}
	transfiguredGemMap := map[string]*gem.Gem{}
	for _, effect := range gemEffects {
		zh := effect.Zh
		if !stringutil.IsASCII(zh) {
			if _, ok := gemZhIdx[zh]; !ok {
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

	// 由于各种原因，需要数据清洗：
	// - 重复数据，相同的zh,en
	// - 脏数据，相同的en，不同的zh，只有一个zh是正确的
	gemEnIdx := map[string]int{}
	uniques := []*gem.Gem{}
	tradeableGemZhSet := map[string]bool{}

	for _, gem := range tradableGems {
		t := formatGemZh(gem["type"].(string))
		text := formatGemZh(gem["text"].(string))

		if strings.HasPrefix(t, "瓦尔：") {
			tradeableGemZhSet[t] = true
		} else {
			tradeableGemZhSet[text] = true
		}
	}

	for _, gem := range gems {
		if removedGemSet[gem.En] {
			continue
		}

		if idx, ok := gemEnIdx[gem.En]; ok {
			old := uniques[idx]
			if old.Zh != gem.Zh {
				if tradeableGemZhSet[old.Zh] && !tradeableGemZhSet[gem.Zh] {
					continue
				}
				if !tradeableGemZhSet[old.Zh] && tradeableGemZhSet[gem.Zh] {
					uniques[idx] = gem
					continue
				}
				fmt.Printf("warning: gem with diff zh: %s %s %s", gem.En, old.Zh, gem.Zh)
			}
		} else {
			gemEnIdx[gem.En] = len(uniques)
			uniques = append(uniques, gem)
		}
	}
	gems = uniques

	data, err := json.MarshalIndent(gems, "", "  ")
	errorutil.QuitIfError(err)

	os.WriteFile(gemsFile, data, 0o666)
}

func formatGemZh(zh string) string {
	zh = strings.Replace(zh, "(", "（", 1)
	return strings.Replace(zh, ")", "）", 1)
}

func main() {
	baseItemTypes := item.LoadBaseItemTypesFromGggpk(baseItemTypesFile, txBaseItemTypesFile)
	gemEffects := gem.LoadGemEffectsFromGgpk(gemEffectsFile, txGemEffectsFile)
	tradableGems := loadGemsFromTradableItemsData()

	initGems(baseItemTypes, gemEffects, tradableGems)
}
