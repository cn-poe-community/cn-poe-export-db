package file

import (
	"io"
	"log"
	"os"

	"golang.org/x/text/encoding/unicode"
	"golang.org/x/text/transform"
)

func ReadFileUTF16(filename string) string {
	// https://stackoverflow.com/a/55632545/21591057
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}

	unicodeReader := transform.NewReader(file, unicode.UTF16(unicode.LittleEndian, unicode.UseBOM).NewDecoder())
	bytes, err := io.ReadAll(unicodeReader)
	if err != nil {
		log.Fatal(err)
	}

	return string(bytes)
}
