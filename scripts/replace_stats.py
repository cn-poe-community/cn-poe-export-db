file = "../src/stats/main.json"
replacement = "../src/stats/main.json.new.json"

import shutil
import os

def replace():
    shutil.copyfile(replacement, file)
    os.remove(replacement)

if __name__ == "__main__":
    replace()