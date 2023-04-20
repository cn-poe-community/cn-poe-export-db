import json
import re

zh_file = "../docs/trade/new/zh_stats.json"
en_file = "../docs/trade/new/en_stats.json"
stat_file = "../src/stats/main.json"


def equipped_label(label: str):
    # 外延、基底、附魔
    return label in ["基底", "Implicit", "外延", "Explicit", "附魔", "Enchant", "古神熔炉", "Crucible"]


def format_stat(stat: str):
    for i in range(100):
        stat = stat.replace("#", f"{{{i}}}", 1)
        if "#" not in stat:
            break
    stat = stat.replace(" (区域)", "")
    stat = stat.replace(" (Local)", "")
    stat = re.sub(r"\s（等阶 \d）", "", stat)
    stat = re.sub(r"\s\(Tier \d\)", "", stat)
    return stat


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def entries_index_by_id(data):
    indexes = {}
    result = data["result"]

    for part in result:
        label = part["label"]
        if (equipped_label(label)):
            entries = part["entries"]
            for entry in entries:
                full_id: str = entry["id"]
                split_result = full_id.split(".")
                id = split_result[-1]
                indexes[id] = entry

    return indexes


def stats_index_by_id(data):
    indexes = {}

    for stat in data:
        id = stat["id"]
        indexes[id] = stat

    return indexes


def append_by_id(ids: list[str]):
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stat_indexes = stats_index_by_id(stat_data)

    new_stats: list = stat_data
    for id in ids:
        if (id in stat_indexes):
            continue
        if id not in zh_indexes:
            print(f"id {id} is not found in zh_stats")
            continue

        if id not in en_indexes:
            print(f"id ${id} is not found in en_stats")
            continue

        zh = format_stat(zh_indexes[id]["text"])
        en = format_stat(en_indexes[id]["text"])

        print("append:", id, zh, en)

        new_stats.append({"id": id, "zh": zh, "en": en})

    with open(f'{stat_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(new_stats, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    ids = ["stat_3357881628", "stat_3224664127", "stat_4184565463",
           "stat_2364563825", "stat_1048825825", "stat_648647905"]
    append_by_id(ids)
