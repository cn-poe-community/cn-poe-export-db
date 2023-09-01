package main

import (
	"bufio"
	"dbutils/pkg/dat"
	"dbutils/pkg/desc"
	"dbutils/pkg/extract"
	"dbutils/pkg/file"
	"dbutils/pkg/gem"
	"dbutils/pkg/stat"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
)

var extractor = "../../tools/ExtractBundledGGPK3/ExtractBundledGGPK3.exe"
var zhContentGgpk = "D:/WeGameApps/流放之路/Content.ggpk"
var contentGgpk = "D:/Program Files (x86)/Grinding Gear Games/Path of Exile/Content.ggpk"

var dat2jsonl = "../../tools/dat2jsonl/dat2jsonl.exe"
var schema = "../../tools/dat2jsonl/schema.min.json"

var saveRoot = "../../docs/ggpk"

var statDescriptionsPath = "metadata/statdescriptions/stat_descriptions.txt"
var zhIndexableSupportGemsPath = "data/simplified chinese/indexablesupportgems.dat64"
var indexableSupportGemsPath = "data/indexablesupportgems.dat64"

var zhStatDescriptionsFile = filepath.Join(saveRoot, "zh", statDescriptionsPath)
var statDescriptionsFile = filepath.Join(saveRoot, "en", statDescriptionsPath)
var zhIndexableSupportGemsFile = filepath.Join(saveRoot, "zh", zhIndexableSupportGemsPath)
var indexableSupportGemsFile = filepath.Join(saveRoot, "en", indexableSupportGemsPath)

var zhIndexableSupportGemsJsonl = zhIndexableSupportGemsFile + ".jsonl"
var indexableSupportGemsJsonl = indexableSupportGemsFile + ".jsonl"

func ExtractFiles() {
	quitIfError(extract.Extract(extractor, zhContentGgpk, statDescriptionsPath, zhStatDescriptionsFile))
	quitIfError(extract.Extract(extractor, contentGgpk, statDescriptionsPath, statDescriptionsFile))
	quitIfError(extract.Extract(extractor, zhContentGgpk, zhIndexableSupportGemsPath, zhIndexableSupportGemsFile))
	quitIfError(extract.Extract(extractor, contentGgpk, indexableSupportGemsPath, indexableSupportGemsFile))

	quitIfError(dat.DatToJsonl(dat2jsonl, zhIndexableSupportGemsFile, "IndexableSupportGems", schema, zhIndexableSupportGemsJsonl))
	quitIfError(dat.DatToJsonl(dat2jsonl, indexableSupportGemsFile, "IndexableSupportGems", schema, indexableSupportGemsJsonl))
}

func quitIfError(err error) {
	if err != nil {
		log.Fatal(err)
	}
}

func CreateStats() {
	statDescContent := file.ReadFileUTF16(statDescriptionsFile)
	zhStatDescContent := file.ReadFileUTF16(zhStatDescriptionsFile)

	statDescContent = hackEnStatDescContent(statDescContent)
	zhStatDescContent = hackZhStatDescContent(zhStatDescContent)

	descs := desc.Load(strings.Split(statDescContent, "\r\n"), strings.Split(zhStatDescContent, "\r\n"))
	descs = removeSkipedDesc(descs)
	hackDescs(descs)

	stats := desc.ToStats(descs)

	stats = appendRandomIndexableSupportStats(stats)

	checkDuplicateZh(stats)

	data, err := json.MarshalIndent(stats, "", "  ")
	if err != nil {
		log.Fatal(err)
	}

	os.WriteFile("../../assets/stats/desc.json", data, 0666)
}

var hackEnStatDescContentEntries = [][2]string{
	{`#|60 "Gain {0} Vaal Soul Per Second during effect" per_minute_to_per_second 1`,
		`60 "Gain {0} Vaal Soul Per Second during effect" per_minute_to_per_second 1`},
	{`1|# "[DNT] Area contains {0} additional Common Chest Marker"`,
		`1 "[DNT] Area contains {0} additional Common Chest Marker"`},
}

func hackEnStatDescContent(content string) string {
	for _, entry := range hackEnStatDescContentEntries {
		if strings.Contains(content, entry[0]) {
			content = strings.ReplaceAll(content, entry[0], entry[1])
		} else {
			log.Printf("hack missed: %v", entry[0])
		}
	}
	return content
}

var hackZhStatDescContentEntries = [][2]string{
	{`#|60 "生效期间每秒获得 {0} 个瓦尔之灵" per_minute_to_per_second 1`,
		`60 "生效期间每秒获得 {0} 个瓦尔之灵" per_minute_to_per_second 1`},
	{`#|-1 "能量护盾全满状态下防止{0:+d}%的被压制法术伤害" reminderstring ReminderTextSuppression`,
		`#|-1 "能量护盾全满状态下防止{0:+d}%的被压制法术伤害的总量" reminderstring ReminderTextSuppression`},
	{`#|-1 "枯萎技能会使干扰持续时间延长 {0}%" negate 1`,
		`#|-1 "枯萎技能会使干扰持续时间缩短 {0}%" negate 1`},
	{`#|-1 "【寒霜爆】技能会使减益效果的持续时间延长 {0}%" negate 1`,
		`#|-1 "【寒霜爆】技能会使减益效果的持续时间缩短 {0}%" negate 1`},
	{`#|-1 "每 10 秒获得 {0}% 的元素伤害增益，持续 4 秒" negate 1`,
		`#|-1 "每 10 秒获得 {0}% 的元素伤害减益，持续 4 秒" negate 1`},
	{`#|-1 "若腐化，则全域暴击率提高 {0}%" negate 1 reminderstring ReminderTextIfItemCorrupted`,
		`#|-1 "若腐化，则全域暴击率降低 {0}%" negate 1 reminderstring ReminderTextIfItemCorrupted`},
	{`1|# "[DNT]该区域会额外出现{0}个普通宝箱标记"`,
		`1 "[DNT]该区域会额外出现{0}个普通宝箱标记"`},
	{"\t1\r\n\t\t# \"图腾放置速度加快 {0}%\"\r\n",
		"\t2\r\n\t\t1|# \"图腾放置速度加快 {0}%\"\r\n#|-1 \"图腾放置速度减慢 {0}%\"\r\n"},
	{"\t\t1|# \"若你近期内有击败敌人，则效果区域扩大 {0}%，最多 50%\" reminderstring ReminderTextRecently\r\n\t\t#|-1 \"若你近期内有击败敌人，则效果区域缩小 {0}%\" negate 1  reminderstring ReminderTextRecently\r\n",
		"\t\t1|# \"若你近期内有击败敌人，则效果区域扩大 {0}%，最多 50%\" reminderstring ReminderTextRecently\r\n\t\t#|-1 \"若你近期内有击败敌人，则效果区域缩小 {0}%，最多 50%\" negate 1  reminderstring ReminderTextRecently\r\n"},
	{`1 "【毒雨】可以额外发射 1 个箭矢"`, `1 "【毒雨】可以额外发射 {0} 个箭矢"`},
	{`1|# "如果诅咒持续时间已经过去 25%，\n则你诅咒的敌人的移动速度被减缓 25%"`, `1|# "如果诅咒持续时间已经过去 25%，\n则你诅咒的敌人的移动速度被减缓 {0}%"`},
}

func hackZhStatDescContent(content string) string {
	for _, entry := range hackZhStatDescContentEntries {
		if strings.Contains(content, entry[0]) {
			content = strings.ReplaceAll(content, entry[0], entry[1])
		} else {
			log.Printf("hack missed: %v", entry[0])
		}
	}
	return content
}

func hackDescs(descs []*desc.Desc) {
	for _, d := range descs {
		// 血影的`每个狂怒球可使攻击速度减慢 4%`，应当为`每个狂怒球可使攻击和施法速度减慢 4%`
		// 与`每个狂怒球可使攻击速度加快 {0}%`,`每个狂怒球可使攻击速度减慢 {0}%`冲突
		// 需要translator进行hack
		if d.Id == "attack_and_cast_speed_+%_per_frenzy_charge" {
			if d.Texts[desc.LangZh][0].Template == "每个狂怒球可使攻击速度加快 {0}%" {
				d.Texts[desc.LangZh][0].Template = "每个狂怒球可使攻击和施法速度加快 {0}%"
			} else {
				log.Panicf("hack missed: %v", d.Id)
			}
			if d.Texts[desc.LangZh][1].Template == "每个狂怒球可使攻击速度减慢 {0}%" {
				d.Texts[desc.LangZh][1].Template = "每个狂怒球可使攻击和施法速度减慢 {0}%"
			} else {
				log.Panicf("hack missed: %v", d.Id)
			}
			continue
		}

		// 戴亚迪安的晨曦的`没有物理伤害`，应当为`不造成物理伤害`
		// 与武器上的`没有物理伤害`词缀产生冲突
		// 受影响物品：戴亚迪安的晨曦，异度天灾武器基底词缀
		// 需要translator进行hack
		if d.Id == "base_deal_no_physical_damage" {
			if d.Texts[desc.LangZh][0].Template == "没有物理伤害" {
				d.Texts[desc.LangZh][0].Template = "不造成物理伤害"
			}
		}
	}
}

var skipedDescIds = map[string]bool{
	// 中文相同英文不同，是地图词缀
	"map_projectile_speed_+%":                     true,
	"map_players_gain_soul_eater_on_rare_kill_ms": true,
	// 中文相同英文不同，是局部词缀
	"local_gem_experience_gain_+%": true,
	"local_accuracy_rating_+%":     true,
	// 中文相同英文不同，是技能说明
	"skill_range_+%": true,
	// 中文相同英文不同，是无效词缀
	"elemental_damage_taken_+%_during_flask_effect": true,
	"global_poison_on_hit":                          true,
	"bleed_on_melee_critical_strike":                true,
	// 中文相同英文不同，但是英文均为有效词缀
	"curse_on_hit_level_warlords_mark":                        true,
	"damage_taken_+%_if_you_have_taken_a_savage_hit_recently": true,
	"immune_to_bleeding":                                      true,
	"onslaught_buff_duration_on_kill_ms":                      true,
	// 中文相同英文不同，不知道正确词缀
	// 【断金之刃】的伤害提高，【断金之刃】的伤害降低
	"shattering_steel_damage_+%": true,
	"lancing_steel_damage_+%":    true,
}

func removeSkipedDesc(descs []*desc.Desc) []*desc.Desc {
	newDescs := make([]*desc.Desc, 0, len(descs))
	for _, d := range descs {
		if !skipedDescIds[d.Id] &&
			!strings.HasPrefix(d.Id, "map_") {
			newDescs = append(newDescs, d)
		}
	}

	return newDescs
}

var randomIndexableSupportStatId1 = "local_random_support_gem_level local_random_support_gem_index"
var randomIndexableSupportStatId2 = "local_random_support_gem_level_1 local_random_support_gem_index_1"

func appendRandomIndexableSupportStats(stats []*stat.Stat) []*stat.Stat {
	newStats := make([]*stat.Stat, 0, len(stats))

	matched := false
	for _, stat := range stats {
		if stat.Id == randomIndexableSupportStatId1 || stat.Id == randomIndexableSupportStatId2 {
			if stat.Zh == "插入的技能石被 {0} 级的【{1}】辅助" && stat.En == "Socketed Gems are Supported by Level {0} {1}" {
				matched = true
			} else {
				log.Fatal("random indexable support stats template changed")
			}
		} else {
			newStats = append(newStats, stat)
		}
	}

	if !matched {
		log.Println("warning: no template of random indexable support stats")
		return stats
	}

	indexableSupportGems := loadIndexableSupportGems()
	for _, gem := range indexableSupportGems {
		newStats = append(newStats, &stat.Stat{
			Id: randomIndexableSupportStatId1,
			Zh: fmt.Sprintf("插入的技能石被 {0} 级的【%s】辅助", gem.Zh),
			En: fmt.Sprintf("Socketed Gems are Supported by Level {0} %s", gem.En),
		})
	}

	return newStats
}

func loadIndexableSupportGems() []*gem.IndexableSupportGem {
	zhEntries := loadIndexableSupportGemJsonl(zhIndexableSupportGemsJsonl)
	enEntries := loadIndexableSupportGemJsonl(indexableSupportGemsJsonl)

	gems, err := mergeIndexableSupportGemJsonl(enEntries, zhEntries)
	if err != nil {
		log.Fatal(err)
	}
	return gems
}

func loadIndexableSupportGemJsonl(filename string) []*gem.IndexableSupportGemJsonlEntry {
	f, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	entries := []*gem.IndexableSupportGemJsonlEntry{}
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if len(line) > 0 {
			entry := &gem.IndexableSupportGemJsonlEntry{}
			err := json.Unmarshal([]byte(line), entry)
			if err != nil {
				log.Fatal(err)
			}
			entries = append(entries, entry)
		}
	}

	return entries
}

func mergeIndexableSupportGemJsonl(enEntryList, zhEntryList []*gem.IndexableSupportGemJsonlEntry) ([]*gem.IndexableSupportGem, error) {
	if len(enEntryList) < len(zhEntryList) {
		return nil, fmt.Errorf("shorter enEntryList")
	}
	result := []*gem.IndexableSupportGem{}
	for i, enEntry := range enEntryList {
		zhEntry := zhEntryList[i]
		result = append(result, &gem.IndexableSupportGem{Index: enEntry.Index, Zh: zhEntry.Name, En: enEntry.Name})
	}
	return result, nil
}

func checkDuplicateZh(stats []*stat.Stat) {
	records := map[string]string{}

	for _, stat := range stats {
		if recordEn, ok := records[stat.Zh]; ok {
			if !strings.EqualFold(recordEn, stat.En) {
				log.Printf("warning diff en of: %v", stat.Zh)
				log.Print(recordEn)
				log.Print(stat.En)
			}
		} else {
			records[stat.Zh] = stat.En
		}
	}
}

/*
 * 从ggpk中提取需要的文件，解析文件，hack解析结果，生成最终的词缀数据库文件。
 *
 */
func main() {
	ExtractFiles()
	CreateStats()
}