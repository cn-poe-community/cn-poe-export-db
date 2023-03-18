import json

zh_file = "../docs/trade/3.20/zh_stats_20230317.json"
en_file = "../docs/trade/3.20/en_stats_20230317.json"
stat_file = "../src/stats/main.json"


def filter_label(label: str):
    return label in ["基底", "Implicit", "外延", "Explicit", "附魔", "Enchant"]


append_blacklist = []
update_blacklist = []


def read_blacklist():
    with open("./diff_db_and_trade_append_blacklist.txt", 'rt', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            slices = line.split()
            if len(slices) > 0:
                id = slices[0]
                if id.startswith("stat_"):
                    append_blacklist.append(id)
    with open("./diff_db_and_trade_update_blacklist.txt", 'rt', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            slices = line.split()
            if len(slices) > 0:
                id = slices[0]
                if id.startswith("stat_") or id.startswith("pseudo_"):
                    update_blacklist.append(id)


def is_equipment_stat(stat: str):
    for keyword in ["怪物", "区域", "地图", "迷雾奖励",
                    "赏金猎人", "夺宝", "珍宝箱", "警报",
                    "封锁", "任务", "钓鱼", "菌潮"]:
        if keyword in stat:
            return False
    return True


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
    zh_set = set()

    for stat in data:
        id = stat["id"]
        zh = stat["zh"]
        if id in indexes:
            indexes[id].append(stat)
        else:
            indexes[id] = [stat]
        zh_set.add(zh)

    return (indexes, zh_set)


def check_not_exist():
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    (stat_indexes, zh_set) = stats_index_by_id(stat_data)

    for id in zh_indexes:
        if id not in en_indexes:
            continue

        if id not in stat_indexes and id not in append_blacklist:
            new_zh: str = format_stat(zh_indexes[id]["text"])
            if not new_zh in zh_set and is_equipment_stat(new_zh):
                print(f"{id} {new_zh}")
            continue


def check_needed_update():
    zh_data = load_json(zh_file)
    en_data = load_json(en_file)
    stat_data = load_json(stat_file)

    zh_indexes = entries_index_by_id(zh_data)
    en_indexes = entries_index_by_id(en_data)
    (stat_indexes, zh_set) = stats_index_by_id(stat_data)

    for id in zh_indexes:
        if id not in en_indexes:
            continue

        if id not in stat_indexes:
            continue
        if id in update_blacklist:
            continue
        else:
            new_zh: str = format_stat(zh_indexes[id]["text"])
            new_en: str = format_stat(en_indexes[id]["text"])

            stats = stat_indexes[id]

            zh = ""
            en = ""
            for stat in stats:
                zh = stat["zh"]
                en = stat["en"]
                if (zh == new_zh):
                    break

            if zh != new_zh:
                print(f"{id} with diff zh:")
                print(f"    {zh}")
                print(f"    {new_zh}")
            if en != new_en:
                print(f"{id} with diff en:")
                print(f"    {en}")
                print(f"    {new_en}")


if __name__ == "__main__":
    read_blacklist()
    
    check_not_exist()
    check_needed_update()
    pass
