package gem

import (
	"dbutils/pkg/utils/errorutil"
	"encoding/json"
	"fmt"
	"os"
)

func LoadIndexableSupportGemsFromGgpk(indexableSupportGemsFile, zhIndexableSupportGemsFile string) []*IndexableSupportGem {
	enEntries := loadGgpkIndexableSupportGems(indexableSupportGemsFile)
	zhEntries := loadGgpkIndexableSupportGems(zhIndexableSupportGemsFile)

	gems, err := mergeGgpkIndexableSupportGems(enEntries, zhEntries)
	errorutil.QuitIfError(err)
	return gems
}

func loadGgpkIndexableSupportGems(filename string) []*GgpkIndexableSupportGem {
	data, err := os.ReadFile(filename)
	errorutil.QuitIfError(err)

	var entries []*GgpkIndexableSupportGem

	json.Unmarshal(data, &entries)

	return entries
}

func mergeGgpkIndexableSupportGems(enEntryList, zhEntryList []*GgpkIndexableSupportGem) ([]*IndexableSupportGem, error) {
	if len(enEntryList) < len(zhEntryList) {
		return nil, fmt.Errorf("shorter enEntryList")
	}
	result := []*IndexableSupportGem{}
	for i, enEntry := range enEntryList {
		zhEntry := zhEntryList[i]
		result = append(result, &IndexableSupportGem{Index: enEntry.Index, Zh: zhEntry.Name, En: enEntry.Name})
	}
	return result, nil
}

func LoadIndexableSkillGemsFromGgpk(indexableSkillGemsFile, zhIndexableSkillGemsFile string) []*IndexableSkillGem {
	enEntries := loadGgpkIndexableSkillGems(indexableSkillGemsFile)
	zhEntries := loadGgpkIndexableSkillGems(zhIndexableSkillGemsFile)

	gems, err := mergeGgpkIndexableSkillGems(enEntries, zhEntries)
	errorutil.QuitIfError(err)
	return gems
}

func loadGgpkIndexableSkillGems(filename string) []*GgpkIndexableSkillGem {
	data, err := os.ReadFile(filename)
	errorutil.QuitIfError(err)

	var entries []*GgpkIndexableSkillGem

	json.Unmarshal(data, &entries)

	return entries
}

func mergeGgpkIndexableSkillGems(enEntryList, zhEntryList []*GgpkIndexableSkillGem) ([]*IndexableSkillGem, error) {
	if len(enEntryList) < len(zhEntryList) {
		return nil, fmt.Errorf("shorter enEntryList")
	}
	result := []*IndexableSkillGem{}
	for i, enEntry := range enEntryList {
		zhEntry := zhEntryList[i]
		result = append(result, &IndexableSkillGem{Index: enEntry.Index, Zh: zhEntry.Name1, En: enEntry.Name1})
	}
	return result, nil
}

func LoadGemEffectsFromGgpk(gemEffectsFile, zhGemEffectsFile string) []*GemEffect {
	enEntries := loadGgpkGemEffects(gemEffectsFile)
	zhEntries := loadGgpkGemEffects(zhGemEffectsFile)

	gems, err := mergeGgpkGemEffects(enEntries, zhEntries)
	errorutil.QuitIfError(err)
	return gems
}

func loadGgpkGemEffects(filename string) []*GgpkGemEffect {
	data, err := os.ReadFile(filename)
	errorutil.QuitIfError(err)

	var entries []*GgpkGemEffect

	json.Unmarshal(data, &entries)

	return entries
}

func mergeGgpkGemEffects(enEntryList, zhEntryList []*GgpkGemEffect) ([]*GemEffect, error) {
	if len(enEntryList) < len(zhEntryList) {
		return nil, fmt.Errorf("shorter enEntryList")
	}

	result := []*GemEffect{}
	for i, enEntry := range enEntryList {
		zhEntry := zhEntryList[i]
		if enEntry.Id != zhEntry.Id {
			errorutil.QuitIfError(fmt.Errorf("id doesnot match of gem effects: %s", zhEntry.Id))
		}
		result = append(result, &GemEffect{Zh: zhEntry.Name, En: enEntry.Name})
	}
	return result, nil
}

func LoadActiveSkillsFromGgpk(gemEffectsFile, zhGemEffectsFile string) []*ActiveSkill {
	enEntries := loadGgpkActiveSkills(gemEffectsFile)
	zhEntries := loadGgpkActiveSkills(zhGemEffectsFile)

	gems, err := mergeGgpkActiveSkills(enEntries, zhEntries)
	errorutil.QuitIfError(err)
	return gems
}

func loadGgpkActiveSkills(filename string) []*GgpkActiveSkill {
	data, err := os.ReadFile(filename)
	errorutil.QuitIfError(err)

	var entries []*GgpkActiveSkill

	json.Unmarshal(data, &entries)

	return entries
}

func mergeGgpkActiveSkills(entryList, zhEntryList []*GgpkActiveSkill) ([]*ActiveSkill, error) {
	entryIdIdx := map[string]*GgpkActiveSkill{}
	zhEntryIdIdx := map[string]*GgpkActiveSkill{}

	for _, entry := range entryList {
		entryIdIdx[entry.Id] = entry
	}

	for _, entry := range zhEntryList {
		zhEntryIdIdx[entry.Id] = entry
	}

	result := []*ActiveSkill{}
	for _, enEntry := range entryList {
		if zhEntry, ok := zhEntryIdIdx[enEntry.Id]; ok {
			result = append(result, &ActiveSkill{Zh: zhEntry.DisplayedName, En: enEntry.DisplayedName})
		}

	}
	return result, nil
}
