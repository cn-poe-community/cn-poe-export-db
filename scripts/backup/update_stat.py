import json

zh_file = "../docs/trade/3.21/zh_stats_20230414.json"
en_file = "../docs/trade/3.21/en_stats_20230414.json"
stat_file = "../src/stats/main.json"


def filter_stat(stat: str):
    return is_ascii(stat)


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
    return "^{}$".format(stat)


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
        if id in indexes:
            indexes[id].append(stat)
        else:
            indexes[id] = [stat]

    return indexes


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def update_ascii_zh_stat():
    zh_data = load_json(zh_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    stat_indexes = stats_index_by_id(stat_data)

    skiped_ids: list = []
    for id, stat in stat_indexes.items():
        old_zh_stat = stat["zh"]
        if filter_stat(old_zh_stat):
            if id not in zh_indexes:
                skiped_ids.append(id)
                continue
            zh_stat = zh_indexes[id]["text"]
            stat_indexes[id]["zh"] = format_stat(zh_stat)

    new_stats: list = []

    for stat in stat_data:
        id = stat["id"]
        if id not in skiped_ids:
            new_stats.append(stat)

    with open(f'{stat_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(new_stats, ensure_ascii=False, indent=4))


def update_diff_zh():
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stat_indexes = stats_index_by_id(stat_data)

    for id, stats in stat_indexes.items():
        if len(stats) > 1:
            continue

        stat = stats[0]

        old_zh_stat: str = stat["zh"]

        if id not in zh_indexes or id not in en_indexes:
            continue
        zh_stat: str = format_stat(zh_indexes[id]["text"])
        en_stat: str = format_stat(en_indexes[id]["text"])

        if (old_zh_stat != zh_stat):
            # print("diff: ", id, old_zh_stat, zh_stat)
            if "药剂生效期间" in old_zh_stat and zh_stat.startswith("^生效期间"):
                print("diff: ", id, old_zh_stat, zh_stat)
                stat["zh"] = zh_stat
                stat["en"] = en_stat

    with open(f'{stat_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(stat_data, ensure_ascii=False, indent=4))


def update_zh_and_en(ids: list[str]):
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stats_indexes = stats_index_by_id(stat_data)

    for id in ids:
        if id not in stats_indexes:
            print(f"{id} not in main.json, skip")
            continue

        stats = stats_indexes[id]
        if len(stats) > 1:
            print(f"{id} mapping multi-stat, skip")
            continue
        if id not in zh_indexes:
            print(f"{id} not in zh_stats, skip")
            continue
        if id not in en_indexes:
            print(f"{id} not in en_stats, skip")
            continue

        zh_stat: str = format_stat(zh_indexes[id]["text"])
        en_stat: str = format_stat(en_indexes[id]["text"])

        stat = stats[0]

        stat["zh"] = zh_stat
        stat["en"] = en_stat
        print(f"update stat {id} success")

    with open(f'{stat_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(stat_data, ensure_ascii=False, indent=4))


def check_diffs_with_zh_prefix(prefix: str):
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stats_indexes = stats_index_by_id(stat_data)

    for id in zh_indexes:
        zh: str = zh_indexes[id]["text"]
        if not zh.startswith(prefix):
            continue

        if id not in stats_indexes:
            print(f"new: {id}")
            return

        if id not in en_indexes:
            print(f"{id} not exist in en_stats")
        en = en_indexes[id]["text"]
        prev_zh = stats_indexes[id][0]["zh"]
        prev_en = stats_indexes[id][0]["en"]

        if (format_stat(zh) != prev_zh):
            print(f"diff zh: {id}")
        if (format_stat(en) != prev_en):
            print(f"diff en: {id}")

def update_zh_en_by_id_prefix(prefix:str):
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    stats_indexes = stats_index_by_id(stat_data)

    for id in zh_indexes:
        if not id.startswith(prefix):
            continue
        if(id not in en_indexes):
            print(f"warning: {id} not in en_stats")
            continue

        if(id in stats_indexes):
            stats = stats_indexes[id]
            if len(stats) > 1:
                print(f"warning: {id} mapping multi-stat, can't be updated")
                continue
        
            new_zh: str = format_stat(zh_indexes[id]["text"])
            new_en: str = format_stat(en_indexes[id]["text"])

            stat = stats[0]
            zh = stat["zh"]
            en = stat["en"]

            if zh != new_zh:
                print(f"update {id} zh")
                stat["zh"] = new_zh
            if en != new_en:
                print(f"update {id} en")
                stat["en"] = new_en
        else:
            print(f"warning: {id} is new, please add it using append_stat.py")
    
    with open(f'{stat_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(stat_data, ensure_ascii=False, indent=4))
            


if __name__ == "__main__":
    ids = ["indexable_support_37", "stat_591645420", "stat_1498186316",
           "stat_1803063132", "stat_1778800422", "stat_884220218"]
    update_zh_and_en(ids)
    #update_zh_en_by_id_prefix("indexable_support")