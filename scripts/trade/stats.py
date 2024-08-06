import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


stats_file = "../../docs/trade/stats"
tx_stats_file = "../../docs/trade/tx/stats"

db_file = "../../assets/stats/trade.json"


def get_stats_from_trade_data(data, group_id_label_filter: set):
    stats = []
    result = data["result"]
    for group in result:
        id = group["id"]
        if group_id_label_filter is not None and id not in group_id_label_filter:
            continue

        entries = group["entries"]
        for entry in entries:
            stats.append(entry)
    return stats

small_passive_skill_option_suffix_legacy = " (Legacy)"
tx_small_passive_skill_option_suffix_legacy = " (遗产)"

def update_small_passive_skills_stats():
    stats_data = load_json(stats_file)
    tx_stats_data = load_json(tx_stats_file)

    group_label = "enchant"

    stats = get_stats_from_trade_data(stats_data, set([group_label]))
    tx_stats = get_stats_from_trade_data(tx_stats_data, set([group_label]))

    tx_stats_idx = {}
    for item in tx_stats:
        id = item["id"]
        tx_stats_idx[id] = item

    small_passive_skills_stat = None
    tx_small_passive_skills_stat = None

    for item in stats:
        id = item["id"]
        text: str = item["text"]

        if text == "Added Small Passive Skills grant: #":
            small_passive_skills_stat = item
            tx_small_passive_skills_stat = tx_stats_idx[id]
            break

    spread_stats = []
    spread_stats_idx = {}
    small_passive_skills_stat_id: str = small_passive_skills_stat["id"]
    if small_passive_skills_stat_id.startswith(group_label+"."):
        small_passive_skills_stat_id = small_passive_skills_stat_id[len(group_label)+1:]

    for option in small_passive_skills_stat["option"]["options"]:
        id = option["id"]
        text: str = option["text"]

        if text.endswith(small_passive_skill_option_suffix_legacy):
            text = text[:len(text)-len(small_passive_skill_option_suffix_legacy)]

        stat = {}
        stat["id"] = f"{small_passive_skills_stat_id}_{id}"

        if "\n" in text:
            zh_pieces = []
            pieces = text.split("\n")
            for piece in pieces:
                zh_pieces.append(small_passive_skills_stat["text"].replace("#", piece))
            stat["en"] = "\n".join(zh_pieces)
        else:
            stat["en"] = small_passive_skills_stat["text"].replace("#", text)

        spread_stats.append(stat)
        spread_stats_idx[stat["id"]] = stat

    for option in tx_small_passive_skills_stat["option"]["options"]:
        id = option["id"]
        text:str = option["text"]

        if text.endswith(tx_small_passive_skill_option_suffix_legacy):
            text = text[:len(text)-len(tx_small_passive_skill_option_suffix_legacy)]


        stat = spread_stats_idx[f"{small_passive_skills_stat_id}_{id}"]

        if "\n" in text:
            zh_pieces = []
            pieces = text.split("\n")
            for piece in pieces:
                zh_pieces.append(tx_small_passive_skills_stat["text"].replace("#", piece))
            stat["zh"] = "\n".join(zh_pieces)
        else:
            stat["zh"] = tx_small_passive_skills_stat["text"].replace("#", text)

    for (i,stat) in enumerate(spread_stats):
        spread_stats[i] = {"id": stat["id"],"zh": stat["zh"],"en": stat["en"]}

    with open(db_file, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(spread_stats, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    update_small_passive_skills_stats()
