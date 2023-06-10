import json
import os

src = "assets/"
dist = "src/assets.js"

def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def json2code(json, variableName):
    if variableName == "requirement_suffixes":
        variableName = "requirementSuffixes"
    return f"export const {variableName} = {json};"


def make_stats():
    stats_folder = os.path.join(src, "stats")
    all_data = []
    # add all stats/*.json
    for file_name in os.listdir(stats_folder):
        if file_name.endswith(".json"):
            data: list = load_json(os.path.join(stats_folder, file_name))
            all_data.extend(data)
    # add jewel-mods
    keystones = load_json(os.path.join(src, "passiveskills", "keystones.json"))
    for keystone in keystones:
        zh = keystone["zh"]
        en = keystone["en"]
        all_data.append({"zh":f"{zh}范围内的天赋可以在\n未连结至天赋树的情况下配置","en":f"Passives in Radius of {en} can be Allocated\nwithout being connected to your tree"})

    all_data = remove_id(all_data)
    all_data = remove_repeats(all_data)

    return all_data

def remove_id(stats):
    return [{"zh": item["zh"], "en": item["en"]} for item in stats]

def remove_repeats(stats):
    stat_list =[]
    stat_map = {}
    for stat in stats:
        zh = stat["zh"]
        en = stat["en"]
        if zh in stat_map:
            old_en = stat_map[zh]["en"]
            if en.casefold()!=old_en.casefold():
                print("warning: same zh but diff en")
                print(f"{zh}")
                print(f"{old_en}")#old
                print(f"{en}")#old
            continue
        stat_list.append(stat)
        stat_map[zh] = stat
    return stat_list

def generate():
    content = []
    for file_name in os.listdir(src):
        source = os.path.join(src, file_name)
        if os.path.isfile(source) and file_name.endswith(".json"):
            data = load_json(source)
            pure_name = file_name[:-5]
            code = json2code(data, pure_name)
            content.append(code)

    for file_name in os.listdir(os.path.join(src, "passiveskills")):
        source = os.path.join(src, "passiveskills", file_name)
        if os.path.isfile(source) and file_name.endswith(".json"):
            data = load_json(source)
            pure_name = file_name[:-5]
            code = json2code(data, pure_name)
            content.append(code)

    stats = make_stats()
    stats_code = json2code(stats, "stats")

    content.append(stats_code)
    with open(dist, 'wt', encoding="utf-8", newline="\n") as f:
        f.write("\n".join(content))

generate()