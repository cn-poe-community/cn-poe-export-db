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
var activeSkillsFile string
var tradableItemsFile string

var txBaseItemTypesFile string
var txGemEffectsFile string
var txActiveSkillsFile string
var txTradableItemsFile string

var gemsFile string
var skillsFile string

// 无效宝石，通过将basetypes中的数据与交易网站中的数据进行diff得到，并通过了人工检查
var invalidGemList = []string{"Righteous Lightning", "Wildfire", "Playtest Spell", "Infernal Sweep",
	"New Blade Vortex", "Capture Monster", "Ignite", "Wand Teleport", "Lightning Channel",
	"Lesser Reduced Mana Cost Support", "Static Tether", "Shadow Blades", "Backstab", "New Shock Nova",
	"Rending Steel", "Ancestral Blademaster", "Fire Weapon", "Icefire", "NewPunishment", "Playtest Slam",
	"Playtest Attack", "Vortex Mine", "Discorectangle Slam", "Elemental Projectiles", "Lightning Circle",
	"Split Projectiles Support", "Damage Infusion", "Summon Skeletons Channelled", "Vaal FireTrap",
	"Spectral Spinning Weapon", "Riptide", "Flammable Shot", "Vaal Soul Harvesting", "Vaal Heavy Strike",
	"Vaal Sweep", "Touch of God", "Vaal Flesh Offering", "Vaal Split Arrow", "Increased Duration Support",
	"Ancestral Protector", "Ancestral Warchief", "Vaal Ancestral Warchief",
}

// 已经遗产的宝石
var legacyGemList = []string{"Item Quantity Support"}

// 非宝石的技能
var nonGemSkillList = []string{"Death Aura", "Envy", "Gluttony of Elements", "Blood Offering", "Blinding Aura",
	"Divine Blessing Support", "Earthbreaker Support",
}

// 已经遗产的技能
var legacySkillList = []string{"Blinding Aura"}

var invalidGemSet = map[string]bool{}
var nonGemSkillSet = map[string]bool{}
var legacyGemSet = map[string]bool{}
var legacySkillSet = map[string]bool{}

func init() {
	c := config.LoadConfig("../config.json")

	baseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/baseitemtypes.dat64.json")
	gemEffectsFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/gemeffects.dat64.json")
	activeSkillsFile = filepath.Join(c.ProjectRoot, "docs/ggpk", "data/activeskills.dat64.json")
	tradableItemsFile = filepath.Join(c.ProjectRoot, "docs/trade/items")

	txBaseItemTypesFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/baseitemtypes.dat64.json")
	txGemEffectsFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/gemeffects.dat64.json")
	txActiveSkillsFile = filepath.Join(c.ProjectRoot, "docs/ggpk/tx", "data/simplified chinese/activeskills.dat64.json")
	txTradableItemsFile = filepath.Join(c.ProjectRoot, "docs/trade/tx/items")

	gemsFile = filepath.Join(c.ProjectRoot, "assets/gems/gems.json")
	skillsFile = filepath.Join(c.ProjectRoot, "assets/gems/skills.json")

	for _, en := range invalidGemList {
		invalidGemSet[en] = true
	}

	for _, en := range nonGemSkillList {
		nonGemSkillSet[en] = true
	}

	for _, en := range legacyGemList {
		legacyGemSet[en] = true
	}

	for _, en := range legacySkillList {
		legacySkillSet[en] = true
	}
}

// 加载可交易宝石，包括中文数据和英文数据
func loadTradableGems() ([]map[string]any, []map[string]any) {
	itemData, err := trade.LoadItemData(tradableItemsFile)
	errorutil.QuitIfError(err)
	txItemData, err := trade.LoadItemData(txTradableItemsFile)
	errorutil.QuitIfError(err)

	var tradableGems []map[string]any
	var txTradableGems []map[string]any

	for _, resultEntry := range itemData.Result {
		if resultEntry.Id == "gem" {
			tradableGems = resultEntry.Entries
			break
		}
	}

	for _, resultEntry := range txItemData.Result {
		if resultEntry.Id == "gem" {
			txTradableGems = resultEntry.Entries
			break
		}
	}

	return tradableGems, txTradableGems
}

func formatGemZh(zh string) string {
	zh = strings.Replace(zh, "(", "（", 1)
	return strings.Replace(zh, ")", "）", 1)
}

func initGems(baseTypes []*item.BaseItemType, gemEffects []*gem.GemEffect,
	tradableGems []map[string]any, txTradableGems []map[string]any) ([]*gem.Gem, map[string]bool) {
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
	transfiguredGemZhIdx := map[string]*gem.Gem{}
	for _, effect := range gemEffects {
		zh := effect.Zh
		if !stringutil.IsASCII(zh) {
			if _, ok := gemZhIdx[zh]; !ok {
				if _, ok := transfiguredGemZhIdx[zh]; !ok {
					g := &gem.Gem{
						En: effect.En,
						Zh: effect.Zh,
					}
					transfiguredGems = append(transfiguredGems, g)
					transfiguredGemZhIdx[g.Zh] = g
				}
			}
		}
	}

	gems = append(gems, transfiguredGems...)

	// 数据清洗：
	// - 重复数据，相同的zh,en
	// - 脏数据，相同的en，不同的zh，只有一个zh是正确的
	// - 未实装的数据，以[DNT]开头
	gemEnIdx := map[string]int{}
	tradableGemSet := map[string]bool{}
	tradableGemZhSet := map[string]bool{}

	uniqueGems := []*gem.Gem{}

	for _, gem := range tradableGems {
		t := formatGemZh(gem["type"].(string))
		var text *string

		if value, ok := gem["text"]; ok {
			textHolder := value.(string)
			text = &textHolder
		}

		tradableGemSet[t] = true

		if !strings.HasPrefix(t, "Vaal ") && text != nil { //改造宝石，非瓦尔版本
			tradableGemSet[*text] = true
		}
	}

	for _, gem := range txTradableGems {
		t := formatGemZh(gem["type"].(string))
		var text *string

		if value, ok := gem["text"]; ok {
			textHolder := formatGemZh(value.(string))
			text = &textHolder
		}

		tradableGemZhSet[t] = true

		if !strings.HasPrefix(t, "瓦尔：") && text != nil { //改造宝石，非瓦尔版本
			tradableGemZhSet[*text] = true
		}
	}

	gemSet := map[string]bool{}

	for _, gem := range gems {
		if invalidGemSet[gem.En] || nonGemSkillSet[gem.En] {
			continue
		}

		if strings.HasPrefix(gem.En, "[DNT]") {
			continue
		}

		if idx, ok := gemEnIdx[gem.En]; ok {
			old := uniqueGems[idx]
			if old.Zh != gem.Zh {
				if tradableGemZhSet[old.Zh] && !tradableGemZhSet[gem.Zh] {
					continue
				}
				if !tradableGemZhSet[old.Zh] && tradableGemZhSet[gem.Zh] {
					uniqueGems[idx] = gem
					continue
				}
				fmt.Printf("warning: gem with diff zh: %s %s %s", gem.En, old.Zh, gem.Zh)
			}
		} else {
			gemEnIdx[gem.En] = len(uniqueGems)

			if legacyGemSet[gem.En] {
				gem.Legacy = true
			}

			if !tradableGemSet[gem.En] {
				log.Printf("warning: un-tradable gem: %s %s", gem.En, gem.Zh)
			}

			uniqueGems = append(uniqueGems, gem)
			gemSet[gem.En] = true
		}
	}

	for en, _ := range tradableGemSet {
		if !gemSet[en] && !invalidGemSet[en] && !nonGemSkillSet[en] {
			log.Printf("warning: missed tradable gem: %s", en)
		}
	}

	return uniqueGems, gemSet
}

func saveGems(gems []*gem.Gem, file string) {
	data, err := json.MarshalIndent(gems, "", "  ")
	errorutil.QuitIfError(err)
	os.WriteFile(file, data, 0o666)
}

func initSkills(gemSet map[string]bool, activeSkills []*gem.ActiveSkill, gemEffects []*gem.GemEffect) []*gem.Gem {
	skills := []*gem.Gem{}

	for _, skill := range activeSkills {
		if skill.En == "" || strings.HasPrefix(skill.En, "[DNT]") || gemSet[skill.En] {
			continue
		}
		skills = append(skills, &gem.Gem{
			En: skill.En,
			Zh: formatGemZh(skill.Zh),
		})
	}

	return skills
}

func main() {
	baseItemTypes := item.LoadBaseItemTypesFromGggpk(baseItemTypesFile, txBaseItemTypesFile)
	gemEffects := gem.LoadGemEffectsFromGgpk(gemEffectsFile, txGemEffectsFile)
	//activeSkills := gem.LoadActiveSkillsFromGgpk(activeSkillsFile, txActiveSkillsFile)
	tradableGems, txTradableGems := loadTradableGems()

	//gems, gemSet := initGems(baseItemTypes, gemEffects, tradableGems, txTradableGems)
	gems, _ := initGems(baseItemTypes, gemEffects, tradableGems, txTradableGems)
	//skills := initSkills(gemSet, activeSkills, gemEffects)

	saveGems(gems, gemsFile)
	//saveGems(skills, skillsFile)
}
