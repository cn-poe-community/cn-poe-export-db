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
    old_file = "../docs/trade/3.20/zh_stats.json"
    new_file = "../docs/trade/3.20/zh_stats_20230215.json"

    old_data = load_json(old_file)
    new_data = load_json(new_file)

    old_entries = entries_index_by_id(old_data)
    new_entries = entries_index_by_id(new_data)

    check_diff_entries(old_entries, new_entries)
