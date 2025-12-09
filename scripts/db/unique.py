import duckdb
from common import CLIENT_GLOBAL, CLIENT_TENCENT, LANG_CHS, LANG_EN, at, read_ndjson, save_ndjson
from db.pair import update_pairs
from export import game, trade

UNIQUES_PATH = "db/uniques.ndjson"


# 遗产的传奇
LEGACY_UNIQUES_BEFORE_TENCENT = [
    "Deshret's Vise Steel Gauntlets",  # 改名物品，旧的在腾讯服之前遗产
    "Dusktoe Leatherscale Boots",  # 改名再改基底，这是最旧的版本，在腾讯服之前遗产
    "Hellbringer Conjurer Gloves",  # 改名再改基底，这是最旧的版本，在腾讯服之前遗产
    "Agnerod Imperial Staff",  # 交易网站上帝国长杖的索引名，实际是4个独立的暗金
]


def unique_names_in_stash_layout():
    """根据UniqueStashLayout表，从Words表中导出传奇名称"""
    table1 = (CLIENT_TENCENT, LANG_CHS, "UniqueStashLayout")
    table2 = (CLIENT_TENCENT, LANG_CHS, "Words")
    table3 = (CLIENT_GLOBAL, LANG_EN, "Words")
    table4 = (CLIENT_TENCENT, LANG_CHS, "UniqueStashTypes")

    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)
    game.load_table(*table4)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)
    duck_name4 = game.duck_table_name(*table4)

    game.create_index(duck_name1, "UniqueStashTypesKey")

    rows = duckdb.sql(f"""SELECT {duck_name2}.Text2, {duck_name3}.Text2, {duck_name2}.Text FROM {duck_name2},{duck_name3}
            WHERE {duck_name2}._index in (
                SELECT WordsKey FROM {duck_name1} INNER JOIN {duck_name4} on {duck_name1}.UniqueStashTypesKey = {duck_name4}._index
                WHERE {duck_name4}.Id not in {"Watchstone", "Map", "HeistContract"}
            )
            AND {duck_name2}.Text = {duck_name3}.Text
        """).fetchall()
    return [{"zh": r[0], "en": r[1], "ref_id": r[2]} for r in rows]


def update_uniques_inner(array: list):
    dat_unique_names = unique_names_in_stash_layout()
    dat_unique_names_zh_idx = {u["zh"]: u for u in dat_unique_names}
    new_uniques_names = {item["zh"]
                         for item in dat_unique_names}-{item["zh"] for item in array}
    for name in new_uniques_names:
        print("info: [uniques] 发现新的暗金：", name)
        u = dat_unique_names_zh_idx[name]
        array.append(
            {"zh": name, "en": u["en"], "baseType": "", "ref_id": u["ref_id"]})

    update_pairs(array, "db/uniques", table_info="Words,Text,Text2",
                 join_fields={"Wordlist"}, filter={"Wordlist": 6})

    global_trade_uniques = trade.equipment_uniques(CLIENT_GLOBAL)
    global_trade_uniques_name_idx = {}
    for u in global_trade_uniques:
        name = u["name"]
        if name not in global_trade_uniques_name_idx:
            global_trade_uniques_name_idx[name] = []
        global_trade_uniques_name_idx[name].append(u)
    for u in array:
        if not u["baseType"]:
            if u["en"] in global_trade_uniques_name_idx:
                matches = global_trade_uniques_name_idx[u["en"]]
                if len(matches) > 1:
                    print("warning: [uniques] 无法更新暗金的基底类型，因为在交易数据中匹配到多个：",
                          u["zh"], u["en"], matches[0]["type"], matches[1]["type"], "...")
                else:
                    u["baseType"] = matches[0]["type"]

    trade_uniques_fullnames = [
        f"{u['name']} {u['type']}" for u in global_trade_uniques]
    exist_uniques_fullnames = [
        f"{u['en']} {u['baseType']}" for u in array if u['baseType']]
    for u in array:
        if not u["baseType"]:
            continue
        full_name = f"{u['en']} {u['baseType']}"
        if full_name not in trade_uniques_fullnames:
            print("warning: [uniques] 暗金在交易数据中不存在：",
                  u['zh'], u['en'], u['baseType'])
    for u in global_trade_uniques:
        full_name = f"{u['name']} {u['type']}"
        if full_name in LEGACY_UNIQUES_BEFORE_TENCENT:
            continue
        if full_name not in exist_uniques_fullnames:
            print("warning: [uniques] 暗金在本地数据中不存在：", u['name'], u['type'])


def check_repeated(uniques: list[dict]):
    names = set()
    for u in uniques:
        zh = u["zh"]
        en = u["en"]
        base_type = u["baseType"]
        name = f"{zh}|{en}|{base_type}"
        if name in names:
            print("warning: [uniques] 重复的暗金数据：", zh, en, base_type)
        else:
            names.add(name)


def update():
    print(f"info: 更新 {UNIQUES_PATH}...")
    uniques = read_ndjson(at(UNIQUES_PATH))
    update_uniques_inner(uniques)
    check_repeated(uniques)
    save_ndjson(at(UNIQUES_PATH), uniques)
