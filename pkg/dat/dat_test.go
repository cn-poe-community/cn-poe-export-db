package dat_test

import (
	"dbutils/pkg/dat"
	"log"
	"testing"
)

func TestDat2Jsonl(t *testing.T) {
	exe := "../../tools/dat2jsonl/dat2jsonl.exe"
	datFile := "IndexableSupportGems.dat64"
	tableName := "IndexableSupportGems"
	schema := "../../tools/dat2jsonl/schema.min.json"
	saveFile := "table.jsonl"

	err := dat.DatToJsonl(exe, datFile, tableName, schema, saveFile)
	if err != nil {
		log.Fatal(err)
	}
}
