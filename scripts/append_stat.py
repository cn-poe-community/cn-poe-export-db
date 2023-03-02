import json

zh_file = "../docs/trade/3.20/zh_stats_20230228.json"
en_file = "../docs/trade/3.20/en_stats_20230228.json"
stat_file = "../src/stats/main.json"


def filter_label(label: str):
    # 外延 or 基底
    return label in ["基底", "Implicit", "外延", "Explicit", "附魔", "Enchant"]


def format_stat(stat: str):
    for i in range(100):
        stat = stat.replace("#", f"{{{i}}}", 1)
        if "#" not in stat:
            break
    stat = stat.replace(" (区域)", "")
    stat = stat.replace(" (Local)", "")
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
        if (filter_label(label)):
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


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


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


def append_by_prefix(prefix: str):
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stat_indexes = stats_index_by_id(stat_data)

    new_stats: list = stat_data
    for id in zh_indexes:
        if id in stat_indexes:
            continue
        if not zh_indexes[id]["text"].startswith(prefix):
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


def append_by_sub_string(sub_string: str):
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stat_indexes = stats_index_by_id(stat_data)

    new_stats: list = stat_data
    for id in zh_indexes:
        if id in stat_indexes:
            continue
        if sub_string not in zh_indexes[id]["text"]:
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
    ids = ["stat_1462364052", "indexable_support_142", "indexable_support_143",
           "indexable_support_144", "indexable_support_145", "indexable_support_146"]
    append_by_id(ids)
