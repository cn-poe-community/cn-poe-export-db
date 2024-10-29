package main

import (
	"dbutils/pkg/config"
	"dbutils/pkg/gem"
	"dbutils/pkg/item"
	"dbutils/pkg/trade"
	"dbutils/pkg/utils/errorutil"
	"dbutils/pkg/utils/stringutil"
	"encoding/json"
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

// 无效技能石，通过将basetypes中的数据与交易网站中的数据进行diff得到
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

// 已经遗产的技能石
var legacyGemList = []string{"Item Quantity Support"}

// 非技能石上的技能
var nonGemSkillList = []string{"Death Aura", "Envy", "Gluttony of Elements", "Blood Offering", "Blinding Aura",
	"Divine Blessing Support", "Earthbreaker Support",
}

// 虽然是非技能石上的技能，但是需要收录
var indexableNonGemSkillList = []string{
	"Death Aura",              //陨命光环
	"Envy",                    //嫉妒
	"Divine Blessing Support", //神圣祝福（辅）
	"Aspect of the Cat",       //猫之势
	"Aspect of the Avian",     //鸟之势
	"Aspect of the Spider",    //蛛之势
	"Aspect of the Crab"}      //蟹之势

// 已经遗产的技能
var legacySkillList = []string{"Blinding Aura"}

var invalidGemSet = map[string]bool{}
var legacyGemSet = map[string]bool{}
var nonGemSkillSet = map[string]bool{}
var indexableNonGemSkillSet = map[string]bool{}
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

	for _, en := range legacyGemList {
		legacyGemSet[en] = true
	}

	for _, en := range nonGemSkillList {
		nonGemSkillSet[en] = true
	}

	for _, en := range indexableNonGemSkillList {
		indexableNonGemSkillSet[en] = true
	}

	for _, en := range legacySkillList {
		legacySkillSet[en] = true
	}
}

// 加载可交易技能石，包括中文数据和英文数据
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

// 从交易网站数据中获取所有技能石名称
func getTradableGemsSet(
	tradableGems []map[string]any,
	txTradableGems []map[string]any) (tradableGemSet map[string]bool, tradableGemZhSet map[string]bool) {

	tradableGemSet = map[string]bool{}
	tradableGemZhSet = map[string]bool{}
	for _, gem := range tradableGems {
		// 交易网站的数据具有如下特征：
		// - type 记录了技能石的名称，改造技能石的字段值仍然为原来的技能石的字段值
		// - text 只有改造技能石有该字段，记录了改造技能石的真正名称
		//
		// 也就是说，普通技能石的名称是type值，改造技能石的名称是text值。
		// 对于瓦尔技能石的改造版本，游戏并没有在名称上进行区分（而是detail有区别），
		// 因此瓦尔技能石的改造版本的名称是交易网站为了区分物品而自定义的，在这里是无效数据
		gemType := gem["type"].(string)
		var gemText *string

		if value, ok := gem["text"]; ok {
			str := value.(string)
			gemText = &str
		}

		tradableGemSet[gemType] = true

		if !strings.HasPrefix(gemType, "Vaal ") && gemText != nil { //改造技能石，非瓦尔版本
			tradableGemSet[*gemText] = true
		}
	}

	for _, gem := range txTradableGems {
		gemType := formatGemZh(gem["type"].(string))
		var gemText *string

		if value, ok := gem["text"]; ok {
			str := formatGemZh(value.(string))
			gemText = &str
		}

		tradableGemZhSet[gemType] = true

		if !strings.HasPrefix(gemType, "瓦尔：") && gemText != nil { //改造技能石，非瓦尔版本
			tradableGemZhSet[*gemText] = true
		}
	}
	return
}

func initGems(baseTypes []*item.BaseItemType, gemEffects []*gem.GemEffect,
	tradableGems []map[string]any, txTradableGems []map[string]any) ([]*gem.Gem, map[string]bool) {
	//从baseTypes中获取技能石
	gems := []*gem.Gem{}
	for _, baseType := range baseTypes {
		// 有效的技能石，其中文名称必然是中文（存在一些未翻译的技能石名称）
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

	//从gemEffects中获取改造技能石
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
	tradableGemSet, tradableGemZhSet := getTradableGemsSet(tradableGems, txTradableGems) //交易网站的数据，用于检查

	cleanGems := []*gem.Gem{} // 清洗后的Gems
	cleanGemSet := map[string]bool{}
	gemEnIdx := map[string]int{}

	for _, gem := range gems {
		// 跳过无效技能石
		if invalidGemSet[gem.En] {
			continue
		}

		//跳过非技能石且不需要索引的技能
		if nonGemSkillSet[gem.En] && !indexableNonGemSkillSet[gem.En] {
			continue
		}

		if strings.HasPrefix(gem.En, "[DNT]") {
			continue
		}

		// 遇到重复的en
		if idx, ok := gemEnIdx[gem.En]; ok {
			old := cleanGems[idx]
			// 如果有不同的zh
			if old.Zh != gem.Zh {
				// 以交易网站的数据为准
				if !tradableGemZhSet[old.Zh] {
					cleanGems[idx] = gem
				}
			}
		} else {
			gemEnIdx[gem.En] = len(cleanGems)

			if legacyGemSet[gem.En] {
				gem.Legacy = true
			}

			if !tradableGemSet[gem.En] && !indexableNonGemSkillSet[gem.En] {
				log.Printf("warning: un-tradable gem: %s %s", gem.En, gem.Zh)
			}

			cleanGems = append(cleanGems, gem)
			cleanGemSet[gem.En] = true
		}
	}

	for en := range tradableGemSet {
		if !cleanGemSet[en] && !invalidGemSet[en] && !nonGemSkillSet[en] {
			log.Printf("warning: missed tradable gem: %s", en)
		}
	}

	return cleanGems, cleanGemSet
}

func saveGems(gems []*gem.Gem, file string) {
	data, err := json.MarshalIndent(gems, "", "  ")
	errorutil.QuitIfError(err)
	os.WriteFile(file, data, 0o666)
}

func initSkills(gemSet map[string]bool, activeSkills []*gem.ActiveSkill) []*gem.Gem {
	skills := []*gem.Gem{}

	// 仅收录需要收录的非技能石技能，且未收录在`gems.json`中
	for _, skill := range activeSkills {
		if !indexableNonGemSkillSet[skill.En] {
			continue
		}

		if gemSet[skill.En] {
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
	activeSkills := gem.LoadActiveSkillsFromGgpk(activeSkillsFile, txActiveSkillsFile)
	tradableGems, txTradableGems := loadTradableGems()

	gems, gemSet := initGems(baseItemTypes, gemEffects, tradableGems, txTradableGems)
	skills := initSkills(gemSet, activeSkills)

	gems = append(gems, skills...)

	saveGems(gems, gemsFile)
	//saveGems(skills, skillsFile)
}
