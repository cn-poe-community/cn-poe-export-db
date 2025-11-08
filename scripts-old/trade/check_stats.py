import json
import re


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


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


desc_file = "../../assets/stats/desc.json"
trade_file = "../../assets/stats/trade.json"
gems_file = "../../assets/gems.json"


def check_indexed_support_in_desc():
    desc = load_json(desc_file)
    trade = load_json(trade_file)

    desc_indexes, desc_zh_set = stats_index_by_id(desc)

    new_trade = []
    for stat in trade:
        zh = stat["zh"]
        if zh in desc_zh_set:
            print(f"repeated: {zh}")
        else:
            new_trade.append(stat)

    with open(f'{trade_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(new_trade, ensure_ascii=False, indent=4))


def check_indexed_support_can_generate():
    gems = load_json(gems_file)
    skill_set = set()
    for gem in gems:
        skills = gem["skills"]
        for skill in skills:
            skill_set.add(skill["zh"])


    trade = load_json(trade_file)
    for stat in trade:
        zh: str = stat["zh"]
        if zh.startswith("插入的技能石被"):
            result = re.findall(r'【(.*)】', zh)
            if len(result) == 0:
                print(f"unexpected: {zh}")
                continue
            skill = result[0]
            if skill+"（辅）" not in skill_set:
                if skill in skill_set:
                    print(f"{skill} has no suffix")
                else:
                    print(f"{skill} is not found")

# check_indexed_support_can_generate()
check_indexed_support_in_desc()