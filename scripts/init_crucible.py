import json
import sys
import re


def crucible_label(label_id: str):
    return label_id == "crucible"


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
        label_id = part["id"]
        if (crucible_label(label_id)):
            entries = part["entries"]
            for entry in entries:
                full_id: str = entry["id"]
                split_result = full_id.split(".")
                id = split_result[-1]
                indexes[id] = entry

    return indexes


new_stats = []


def init(en_entries, zh_entries):
    for id in en_entries:
        if (id not in zh_entries):
            print(f"{id} does not have zh data")
            continue

        zh_text = format_stat(zh_entries[id]["text"])
        en_text = format_stat(en_entries[id]["text"])

        stat = {"id": id}

        stat["zh"] = zh_text
        stat["en"] = en_text
        new_stats.append(stat)

        # crucible mods should add all sub mods into stats
        if "\n" in zh_text:
            zh_sub_texts = zh_text.split("\n")
            en_sub_texts = en_text.split("\n")
            for i, zh_sub_text in enumerate(zh_sub_texts):
                en_sub_text = en_sub_texts[i]
                stat = {"id": id}
                stat["zh"] = zh_sub_text
                stat["en"] = en_sub_text
                new_stats.append(stat)


if __name__ == "__main__":
    zh_file = "../docs/trade/new/zh_stats.json"
    en_file = "../docs/trade/new/en_stats.json"

    zh_data = load_json(zh_file)
    en_data = load_json(en_file)

    zh_entries = entries_index_by_id(zh_data)
    en_entries = entries_index_by_id(en_data)

    init(zh_entries=zh_entries,en_entries=en_entries)

    db_path = "../src/stats/crucible.json"

    with open(f'{db_path}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(new_stats, ensure_ascii=False, indent=4))
