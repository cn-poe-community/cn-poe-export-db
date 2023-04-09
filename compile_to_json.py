import json
import os
import shutil


def copyDir(src, dist):
    os.mkdir(dist, 0o666)
    for file_name in os.listdir(src):
        source = os.path.join(src, file_name)
        destination = os.path.join(dist, file_name)
        if os.path.isfile(source):
            shutil.copy(source, destination)
        elif os.path.isdir(source):
            copyDir(source, destination)


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def empty_dist_and_copy_file():
    try:
        shutil.rmtree(dist)
    except:
        print("dist is cleaned")

    os.mkdir(dist, 0o666)

    for file_name in os.listdir(src):
        if(file_name == stats_folder_name):
            continue

        source = os.path.join(src, file_name)
        destination = os.path.join(dist, file_name)
        if os.path.isfile(source):
            shutil.copy(source, destination)
        elif os.path.isdir(source):
            copyDir(source, destination)


def compileStat():
    stats_folder = os.path.join(src, stats_folder_name)
    all_data = []
    for file_name in os.listdir(stats_folder):
        if file_name.endswith(".json"):
            data: list = load_json(os.path.join(stats_folder, file_name))
            all_data.extend(data)

    with open(os.path.join(dist, "stats.json"), 'wt', encoding="utf-8") as f:
        f.write(json.dumps(all_data, ensure_ascii=False, indent=4))


src = "src"
dist = "dist/json"
stats_folder_name = "stats"


empty_dist_and_copy_file()
compileStat()
