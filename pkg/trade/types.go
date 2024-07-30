package trade

import (
	"encoding/json"
	"os"
)

type ItemsData struct {
	Result []ItemsDataResultEntry `json:"result"`
}

type ItemsDataResultEntry struct {
	Id      string           `json:"id"`
	Label   string           `json:"label"`
	Entries []map[string]any `json:"entries"`
}

func LoadItemData(itemsDataFile string) (*ItemsData, error) {
	data, err := os.ReadFile(itemsDataFile)
	if err != nil {
		return nil, err
	}

	var itemsData ItemsData

	err = json.Unmarshal(data, &itemsData)
	if err != nil {
		return nil, err
	}

	return &itemsData, nil
}
