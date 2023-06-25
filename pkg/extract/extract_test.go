package extract_test

import (
	"dbutils/pkg/extract"
	"os"
	"testing"
)

func TestExtract(t *testing.T) {
	t.Log(os.Getwd())
	pathToExtractor := "../../tools/ExtractBundledGGPK3/ExtractBundledGGPK3.exe"
	pathToGgpk := `D:\WeGameApps\流放之路\Content.ggpk`
	pathToExtract := "Metadata/StatDescriptions/stat_descriptions.txt"
	pathToSave := `F:\stat_descriptions.txt`

	err := extract.Extract(pathToExtractor, pathToGgpk, pathToExtract, pathToSave)
	if err != nil {
		t.Error(err)
	}
}
