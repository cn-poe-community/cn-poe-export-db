package dat

import (
	"os"
	"os/exec"
)

func DatToJsonl(exe string, dat string, tableName string, schema string, saveFile string) error {
	cmd := exec.Command(exe, "--dat", dat, "--table-name", tableName, "--schema", schema)

	cmd.Stderr = os.Stderr
	outfile, err := os.Create(saveFile)
	if err != nil {
		return err
	}
	defer outfile.Close()
	cmd.Stdout = outfile

	return cmd.Run()
}
