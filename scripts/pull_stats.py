import json
import sys
import re


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


key_to_label = {}


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
                key_to_label[id] = label

    return indexes


def stats_index_by_id(data):
    indexes = {}

    for stat in data:
        id = stat["id"]
        if id in indexes:
            indexes[id].append(stat)
        else:
            indexes[id] = [stat]

    return indexes


def diff(old_entries, new_entries):
    new_stat_ids = []
    removed_stat_ids = []
    updated_stat_ids = []
    for id, _ in old_entries.items():
        if id not in new_entries:
            removed_stat_ids.append(id)
    for id, entry in new_entries.items():
        if id not in old_entries:
            new_stat_ids.append(id)
            continue
        new_text = entry["text"]
        old_text = old_entries[id]["text"]
        if new_text != old_text:
            updated_stat_ids.append(id)
    return [removed_stat_ids, updated_stat_ids, new_stat_ids]


new_stats = []
removed_ids = []


def pull_by_en_diff(db, diff, en_entries, zh_entries):
    if command == "update":
        for id in diff[1]:
            if id not in db:
                print(f"{id} not in db, skipped")
                continue
            stats = db[id]
            if (len(stats) > 1):
                print(f"{id} mapping mult stats, skipped")
                continue
            stat = stats[0]
            stat["zh"] = format_stat(zh_entries[id]["text"])
            stat["en"] = format_stat(en_entries[id]["text"])
    if command == "add":
        for id in diff[2]:
            if (id not in zh_entries):
                print(f"{id} does not have zh data")
                continue

            stat = {"id": id}
            stat["zh"] = format_stat(zh_entries[id]["text"])
            stat["en"] = format_stat(en_entries[id]["text"])
            new_stats.append(stat)

            label = key_to_label[id]
            # crucible mods should add all sub mods into stats
            if label in ["古神熔炉", "Crucible"]:
                zh_text = format_stat(zh_entries[id]["text"])
                en_text = format_stat(en_entries[id]["text"])
                if "\n" in zh_text:
                    zh_sub_texts = zh_text.split("\n")
                    en_sub_texts = en_text.split("\n")
                    for i, zh_sub_text in enumerate(zh_sub_texts):
                        en_sub_text = en_sub_texts[i]
                        stat = {"id": id}
                        stat["zh"] = zh_sub_text
                        stat["en"] = en_sub_text
                        new_stats.append(stat)
    if command == "del":
        for id in diff[0]:
            removed_ids.append(id)


def pull_by_zh_diff(db, diff, en_entries, zh_entries):
    if command == "update":
        for id in diff[1]:
            if id not in db:
                print(f"{id} not in db, skipped")
                continue
            stats = db[id]
            if (len(stats) > 1):
                print(f"{id} mapping mult stats, skipped")
                continue
            stat = stats[0]
            stat["zh"] = format_stat(zh_entries[id]["text"])
    if command == "add":
        for id in diff[2]:
            if (id not in en_entries):
                print(f"{id} does not have en data")
                continue
            stat = {"id": id}
            stat["zh"] = format_stat(zh_entries[id]["text"])
            stat["en"] = format_stat(en_entries[id]["text"])
            new_stats.append(stat)

            label = key_to_label[id]
            # crucible mods should add all sub mods into stats
            if label in ["古神熔炉", "Crucible"]:
                zh_text = format_stat(zh_entries[id]["text"])
                en_text = format_stat(en_entries[id]["text"])
                if "\n" in zh_text:
                    zh_sub_texts = zh_text.split("\n")
                    en_sub_texts = en_text.split("\n")
                    for i, zh_sub_text in enumerate(zh_sub_texts):
                        en_sub_text = en_sub_texts[i]
                        stat = {"id": id}
                        stat["zh"] = zh_sub_text
                        stat["en"] = en_sub_text
                        new_stats.append(stat)
    if command == "del":
        for id in diff[0]:
            removed_ids.append(id)


command = ""
if __name__ == "__main__":
    n = len(sys.argv)
    if n == 1:
        command = "print"
    command = sys.argv[1]
    if command not in ["del", "update", "add"]:
        command = "print"

    old_zh_file = "../docs/trade/old/zh_stats.json"
    old_en_file = "../docs/trade/old/en_stats.json"

    new_zh_file = "../docs/trade/new/zh_stats.json"
    new_en_file = "../docs/trade/new/en_stats.json"

    old_zh_data = load_json(old_zh_file)
    old_en_data = load_json(old_en_file)

    new_zh_data = load_json(new_zh_file)
    new_en_data = load_json(new_en_file)

    old_zh_entries = entries_index_by_id(old_zh_data)
    old_en_entries = entries_index_by_id(old_en_data)

    new_zh_entries = entries_index_by_id(new_zh_data)
    new_en_entries = entries_index_by_id(new_en_data)

    diff_en = diff(old_en_entries, new_en_entries)
    diff_zh = diff(old_zh_entries, new_zh_entries)
    for i in range(len(diff_zh)):
        diff_zh[i] = [id for id in diff_zh[i] if id not in diff_en[i]]

    db_path = "../src/stats/main.json"
    db: list = load_json(db_path)

    stats = stats_index_by_id(db)

    if command == "print":
        print("print is no implemented")
        print("please use `pull del`,`pull update`,`pull add`")
        sys.exit()

    print("pull by en diff")
    pull_by_en_diff(stats, diff_en, new_en_entries, new_zh_entries)
    print("pull by zh diff")
    pull_by_zh_diff(stats, diff_zh, new_en_entries, new_zh_entries)

    if command == "add":
        db.extend(new_stats)
    if command == "del":
        db = [stat for stat in db if stat["id"] not in removed_ids]

    with open(f'{db_path}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(db, ensure_ascii=False, indent=4))
