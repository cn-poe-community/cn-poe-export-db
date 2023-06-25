package extract

import (
	"os"
	"os/exec"
)

func Extract(pathToExtractor string, pathToGgpk string, pathToExtract string, pathToSave string) error {
	cmd := exec.Command(pathToExtractor, pathToGgpk, pathToExtract, pathToSave)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
