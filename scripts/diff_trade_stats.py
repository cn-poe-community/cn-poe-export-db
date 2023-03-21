import json


def filter_label(label: str):
    # 外延 or 基底
    return label in ["基底", "Implicit", "外延", "Explicit", "附魔", "Enchant"]


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


def check_diff_entries(old_entries, new_entries):
    for id, _ in old_entries.items():
        if id not in new_entries:
            print(f"{id} has been deleted")

    for id, new_entries in new_entries.items():
        if id not in old_entries:
            print(f"{id} has been added")
            continue
        new_text = new_entries["text"]
        old_text = old_entries[id]["text"]
        if new_text != old_text:
            print(f"{id} has been updated:")
            print(f"{old_text}")
            print(f"{new_text}")


if __name__ == "__main__":
    old_zh_file = "../docs/trade/3.20/zh_stats_20230317.json"
    old_en_file = "../docs/trade/3.20/en_stats_20230317.json"

    new_zh_file = "../docs/trade/3.20/zh_stats_20230321.json"
    new_en_file = "../docs/trade/3.20/en_stats_20230321.json"

    old_zh_data = load_json(old_zh_file)
    old_en_data = load_json(old_en_file)

    new_zh_data = load_json(new_zh_file)
    new_en_data = load_json(new_en_file)

    old_zh_entries = entries_index_by_id(old_zh_data)
    old_en_entries = entries_index_by_id(old_en_data)

    new_zh_entries = entries_index_by_id(new_zh_data)
    new_en_entries = entries_index_by_id(new_en_data)

    check_diff_entries(old_zh_entries, new_zh_entries)
    check_diff_entries(old_en_entries, new_en_entries)
