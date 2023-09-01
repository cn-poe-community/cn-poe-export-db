package main

import (
	"bufio"
	"dbutils/pkg/dat"
	"dbutils/pkg/extract"
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"strings"
)

var extractor = "../../tools/ExtractBundledGGPK3/ExtractBundledGGPK3.exe"
var contentGgpk = "D:/Program Files (x86)/Grinding Gear Games/Path of Exile/Content.ggpk"
var zhContentGgpk = "D:/WeGameApps/流放之路/Content.ggpk"

var dat2jsonl = "../../tools/dat2jsonl/dat2jsonl.exe"
var schema = "../../tools/dat2jsonl/schema.min.json"

var saveRoot = "../../docs/ggpk"

var baseItemTypesPath = "data/baseitemtypes.dat64"
var zhBaseItemTypesPath = "data/simplified chinese/baseitemtypes.dat64"

var baseItemTypesFile = filepath.Join(saveRoot, "en", baseItemTypesPath)
var zhBaseItemTypesFile = filepath.Join(saveRoot, "zh", zhBaseItemTypesPath)

var baseItemTypesJsonl = baseItemTypesFile + ".jsonl"
var zhBaseItemTypesJsonl = zhBaseItemTypesFile + ".jsonl"

var tattoosFile = "../../assets/tattoos.json"

func extractFiles() {
	quitIfError(extract.Extract(extractor, contentGgpk, baseItemTypesPath, baseItemTypesFile))
	quitIfError(extract.Extract(extractor, zhContentGgpk, zhBaseItemTypesPath, zhBaseItemTypesFile))

	quitIfError(dat.DatToJsonl(dat2jsonl, baseItemTypesFile, "BaseItemTypes", schema, baseItemTypesJsonl))
	quitIfError(dat.DatToJsonl(dat2jsonl, zhBaseItemTypesFile, "BaseItemTypes", schema, zhBaseItemTypesJsonl))
}

func quitIfError(err error) {
	if err != nil {
		log.Fatal(err)
	}
}

type BaseItemTypeJsonlEntry struct {
	HASH32 int32
	Name   string
}

type BaseItemType struct {
	HASH32 int32
	En     string
	Zh     string
}

type Tattoo struct {
	En string `json:"en"`
	Zh string `json:"zh"`
}

var enTattooKeyword = "Tattoo"
var zhTattooKeyword = "文身"

func initTattoos() {
	baseItemTypes := loadBaseItemTypes()
	tattoos := []*Tattoo{}
	for _, itemType := range baseItemTypes {
		if strings.Contains(itemType.En, enTattooKeyword) && strings.Contains(itemType.Zh, zhTattooKeyword) {
			tattoos = append(tattoos, &Tattoo{
				En: itemType.En,
				Zh: itemType.Zh,
			})
		}
	}

	data, err := json.MarshalIndent(tattoos, "", "  ")
	if err != nil {
		log.Fatal(err)
	}

	os.WriteFile(tattoosFile, data, 0666)
}

func loadBaseItemTypes() []*BaseItemType {
	enEntries := loadBaseItemTypeJsonl(baseItemTypesJsonl)
	zhEntries := loadBaseItemTypeJsonl(zhBaseItemTypesJsonl)

	baseItemTypes, err := mergeIndexableSupportGemJsonl(enEntries, zhEntries)
	if err != nil {
		log.Fatal(err)
	}
	return baseItemTypes
}

func loadBaseItemTypeJsonl(filename string) []*BaseItemTypeJsonlEntry {
	f, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	entries := []*BaseItemTypeJsonlEntry{}
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if len(line) > 0 {
			entry := &BaseItemTypeJsonlEntry{}
			err := json.Unmarshal([]byte(line), entry)
			if err != nil {
				log.Fatal(err)
			}
			entries = append(entries, entry)
		}
	}

	return entries
}

func mergeIndexableSupportGemJsonl(enEntryList, zhEntryList []*BaseItemTypeJsonlEntry) ([]*BaseItemType, error) {
	enEntriesIndexByHash32 := map[int32]*BaseItemTypeJsonlEntry{}
	for _, entry := range enEntryList {
		enEntriesIndexByHash32[entry.HASH32] = entry
	}

	result := []*BaseItemType{}

	for _, zhEntry := range zhEntryList {
		baseItemType := &BaseItemType{
			HASH32: zhEntry.HASH32,
			Zh:     zhEntry.Name,
		}
		hash32 := zhEntry.HASH32
		if enEntry, ok := enEntriesIndexByHash32[hash32]; ok {
			baseItemType.En = enEntry.Name
		}

		result = append(result, baseItemType)
	}

	return result, nil
}

func main() {
	extractFiles()
	initTattoos()
}
