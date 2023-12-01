package dat_test

import (
	"dbutils/pkg/dat"
	"log"
	"testing"
)

func TestDat2Jsonl(t *testing.T) {
	exe := "../../tools/poedat/poedat.exe"
	datFile := "../../docs/ggpk/zh/data/simplified chinese/IndexableSupportGems.dat64"
	tableName := "IndexableSupportGems"
	schema := "../../tools/poedat/schema.min.json"

	err := dat.DatToJson(exe, datFile, tableName, schema)
	if err != nil {
		log.Fatal(err)
	}
}
