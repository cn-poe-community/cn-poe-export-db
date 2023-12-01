package dat

import (
	"os"
	"os/exec"
)

func DatToJson(exe string, dat string, tableName string, schema string) error {
	cmd := exec.Command(exe, "-d", dat, "-t", tableName, "-s", schema)

	cmd.Stderr = os.Stderr
	cmd.Stdout = os.Stdout

	return cmd.Run()
}
