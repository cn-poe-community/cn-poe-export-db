package main

import (
	"bytes"
	"log"
	"os"
	"path/filepath"

	"golang.org/x/text/encoding/unicode"
)

func search(file string, text []byte) bool {
	data, err := os.ReadFile(file)
	if err != nil {
		panic(err)
	}
	return bytes.Contains(data, text)
}

func main() {
	root := "E:\\export"
	text := "uniqueitem"
	//text_utf8_bytes := []byte(text)
	text_uft16le_bytes := []byte{}

	{
		encoder := unicode.UTF16(unicode.LittleEndian, unicode.IgnoreBOM).NewEncoder()
		var err error
		text_uft16le_bytes, err = encoder.Bytes([]byte(text))
		if err != nil {
			panic(err)
		}
	}

	var scan func(string)

	scan = func(root string) {
		entries, err := os.ReadDir(root)
		if err != nil {
			panic(err)
		}

		for _, entry := range entries {
			fullPath := filepath.Join(root, entry.Name())
			if entry.IsDir() {
				scan(fullPath)
			} else {
				if search(fullPath, text_uft16le_bytes) {
					log.Printf("utf16le %v", fullPath)
				}
			}
		}
	}

	scan(root)
}
