import json
import os
from pathlib import Path
import re
import subprocess
import sys

import duckdb
# =============================================== 全局配置

POB2_PATH = "D:/AppsInDisk/PoeCharm2-20250918_2/PathOfBuildingCommunity-PoE2"
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent

# =============================================== Const

# 语言
CHS = "Simplified Chinese"
EN = "English"

# 服务器
GGG = "global"
TX = "tencent"

# =============================================== Utils


def must_parent(path: str) -> None:
    '''确保文件所在路径存在, 常用于写入文件时，避免父目录不存在而抛出异常'''
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_json(file: str):
    '''读取json文件'''
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def save_json(file: str, data) -> None:
    '''保存json文件'''
    must_parent(file)
    with open(file, 'wt', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def at(*paths: str) -> str:
    '''获取相对于项目目录的路径，支持多个路径参数'''
    return os.path.join(PROJECT_ROOT, *paths)


def is_number(s):
    """检查字符串是否是数字（最通用的方法）"""
    try:
        float(s)  # 尝试转换为float
        return True
    except ValueError:
        return False


def sql_escape(s: str) -> str:
    """SQL字符串转义"""
    return s.replace("'", "''")

# =============================================== Tables


def table_path(client: str, lang: str, table: str) -> str:
    '''获取表格文件路径'''
    return at("export/game", client, 'tables', lang, f"{table}.json")


loaded_tables = set()


def duck_table_name(client: str, lang: str, table: str):
    return f"{client}_{lang}_{table}".replace(" ", "_").lower()


def load_table(client: str, lang: str, table: str):
    file = table_path(client, lang, table)
    duck_name = duck_table_name(client, lang, table)

    if duck_name in loaded_tables:
        return
    loaded_tables.add(duck_name)
    duckdb.sql(f"""
    CREATE TABLE {duck_name} AS
        SELECT * FROM '{file}';
    """)

# =============================================== trade


def trade_file_path(client: str, name: str) -> str:
    '''获取交易网站的文件路径'''
    return at("export/trade", client, f"{name}.json")


ITEMS_EQUIPEMNT_IDS = ["accessory", "armour", "flask", "jewel", "weapon"]


def export_trade_uniques(client):
    """从交易网站数据导出传奇，参数client指定客户端"""
    data = read_json(trade_file_path(client, "items"))
    array = []
    for category in data["result"]:
        if category["id"] not in ITEMS_EQUIPEMNT_IDS:
            continue

        entries = category["entries"]
        for entry in entries:
            if "flags" not in entry or "unique" not in entry["flags"] or not entry["flags"]["unique"]:
                continue
            if entry["name"] in LEGACY_UNIQUE_BEFORE_0_3:
                continue
            u = {"name": entry["name"], "type": entry["type"]}
            array.append(u)
    return array


def load_trade_table(client, table):
    """
    将数据存在数据库中，便于处理。支持以下表：

    - uniques，数据源自export_trade_uniques()
    """
    duck_name = f"trade_{client}_{table}".replace(" ", "_").lower()

    if duck_name in loaded_tables:
        return
    loaded_tables.add(duck_name)

    data = []
    if table == "uniques":
        data = export_trade_uniques(client)
    else:
        print(f"error: [trade] 不支持的交易表 {client} {table}")
        return

    # 由于duckdb的引擎限制，这里将数据写入文件再进行读取
    # https://duckdb.org/docs/stable/clients/python/data_ingestion#directly-accessing-dataframes-and-arrow-objects
    file = at("scripts/duckdb", f"{duck_name}.json")
    save_json(file, data)
    duckdb.sql(f"""
    CREATE TABLE {duck_name} AS
        SELECT * FROM '{file}';
    """)


def clean_duckdb_files():
    """清理duckdb的数据库文件"""
    duckdb_dir = at("scripts/duckdb")
    if not os.path.exists(duckdb_dir):
        return
    for file in os.listdir(duckdb_dir):
        if file.endswith(".duckdb") or file.endswith(".json"):
            os.remove(os.path.join(duckdb_dir, file))

# =============================================== POB


def get_pob_latest_tree_version() -> str:
    wd = at("scripts/luajit")
    env = os.environ.copy()
    env["LUA_PATH"] = f"{POB2_PATH}/?.lua;{POB2_PATH}/lua/?.lua;"

    result = subprocess.run(["luajit/luajit.exe", "-e", "local m = require 'GameVersions'; print(latestTreeVersion)"],
                            capture_output=True,
                            text=True,
                            cwd=wd,
                            env=env)
    if result.stderr.strip() != "":
        raise Exception(f"POB: 获取最新天赋树版本失败 {result.stderr.strip()}")
    return result.stdout.strip()


def get_pob_tree(version: str):
    wd = at("scripts/luajit")
    env = os.environ.copy()
    env["LUA_PATH"] = f"{POB2_PATH}/lua/?.lua;{POB2_PATH}/TreeData/{version}/?.lua;"

    result = subprocess.run(["luajit/luajit.exe", "-e", "local j = require 'dkjson';local t = require 'tree'; print(j.encode(t))"],
                            capture_output=True,
                            text=True,
                            cwd=wd,
                            env=env)
    if result.stderr.strip() != "":
        raise Exception(f"POB: 获取最新天赋树失败: {result.stderr.strip()}")
    return json.loads(result.stdout.strip())

# =============================================== Tasks

# ============= Task: 生成creator所需的数据 ============


def create_creator_tree():
    '''creator所需的POB天赋树'''
    tree_version = get_pob_latest_tree_version()
    pob_tree = get_pob_tree(tree_version)

    slim_tree = {k: pob_tree[k] for k in pob_tree if k in ["classes"]}

    for c in slim_tree["classes"]:
        if "background" in c:
            del c["background"]
        if "ascendancies" in c:
            for a in c["ascendancies"]:
                if "background" in a:
                    del a["background"]

    saved = at("assets/pob2/tree.json")
    must_parent(saved)
    with open(saved, 'wt', encoding='utf-8') as f:
        json.dump(slim_tree, f, ensure_ascii=False, indent=2)


# ======== Task: 更新assets/poe2/attrs,props,reqs =========

def export_all(table_info: str) -> list:
    '''导出表中的所有内容。table_info采用`表名,主键名,字段名`的格式。'''
    [table_name, pkey_name, field_name] = table_info.split(",")

    table1 = (TX, CHS, table_name)
    table2 = (GGG, EN, table_name)

    load_table(*table1)
    load_table(*table2)

    duck_name1 = duck_table_name(*table1)
    duck_name2 = duck_table_name(*table2)

    rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name},{duck_name1}.{field_name},{duck_name2}.{field_name}
        FROM {duck_name1}
        LEFT JOIN {duck_name2} ON {duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}""").fetchall()

    return [{"id": row[0], "zh": row[1], "en": row[2]} for row in rows]


def update_required(array: list[dict], table_info: str, logger: str, field_info="id,zh,en"):
    '''
    只更新需要的内容。array为需要更新的数据，table_info采用`表名,主键名,字段名`的格式，
    field_info采用`主键在项中的字段名,中文内容在项中的字段名,英文内容在项中的字段名`。

    用于更新properties,requirements,attributes的通用函数，包括它们的值。

    这三类的主要来源是ClientString表，它们结构类似，维护方式类似（半自动维护）。

    更新有两个含义：
    1. 当中文或英文发生改变时，自动更新中文或英文。
    2. 新增项只需要手动添加中文(zh)，自动填充id和en。

    这个函数也被用于更新uniques，因此维护时注意通用性。

    为了保证JSON格式的一致性（字段顺序），当手动添加中文时(zh)，添加空的id和en。
    '''

    [table_name, pkey_name, field_name] = table_info.split(",")
    [id_field, zh_field, en_field] = field_info.split(",")

    table1 = (TX, CHS, table_name)
    table2 = (GGG, EN, table_name)

    load_table(*table1)
    load_table(*table2)

    duck_name1 = duck_table_name(*table1)
    duck_name2 = duck_table_name(*table2)

    def add_id(entry):
        if id_field in entry and entry[id_field]:
            return

        # 确保字段存在，避免访问错误
        if zh_field not in entry:
            entry[zh_field] = ""
        if en_field not in entry:
            entry[en_field] = ""

        rows = []

        # 如果中英文都存在，那么两者同时匹配
        if en_field in entry and entry[en_field] and zh_field in entry and entry[zh_field]:
            rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name} FROM {duck_name1}
            LEFT JOIN {duck_name2} ON {duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}
            WHERE {duck_name1}.{field_name} == '{entry[zh_field]}' and {duck_name2}.{field_name} == '{entry[en_field]}'""").fetchall()
        elif zh_field in entry and entry[zh_field]:  # 只匹配中文
            rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name} FROM {duck_name1}
            WHERE {duck_name1}.{field_name} == '{entry[zh_field]}'""").fetchall()
        elif en_field in entry and entry[en_field]:  # 只匹配英文
            rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name} FROM {duck_name1}
            LEFT JOIN {duck_name2} ON {duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}
            WHERE {duck_name2}.{field_name} == '{entry[en_field]}'""").fetchall()

        if len(rows) > 1:
            print(
                f"warning: [{logger}] {entry[zh_field]},{entry[en_field]} 在 {table_name} 表中匹配多个记录 {rows[0][0]}, {rows[1][0]}...")
        if len(rows) == 1:
            entry[id_field] = rows[0][0]

    def update_text(entry):
        if id_field not in entry or not entry[id_field]:
            return
        id = entry[id_field]
        row = duckdb.sql(f"""SELECT {duck_name1}.{field_name},{duck_name2}.{field_name} FROM {duck_name1}
        LEFT JOIN {duck_name2} ON {duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}
        WHERE {duck_name1}.{pkey_name} == '{sql_escape(id)}'""").fetchone()

        if row == None:
            return
        if zh_field not in entry:
            entry[zh_field] = ""
        if en_field not in entry:
            entry[en_field] = ""
        if entry[zh_field] != row[0] or entry[en_field] != row[1]:
            old_zh = entry[zh_field]
            old_en = entry[en_field]
            print(
                f"info: [{logger}] 更新 '{old_zh}','{old_en}'  -> '{row[0]}','{row[1]}'")
            entry[zh_field] = row[0]
            entry[en_field] = row[1]

    def update_values(entry):
        if "values" in entry:
            ti = table_info
            if "values_table" in entry:
                ti = entry["values_table"]
            update_required(
                entry["values"], ti, f"{logger} values")

    for entry in array:
        add_id(entry)
        update_text(entry)
        update_values(entry)


def check_duplicate_zhs(array: list[dict], logger: str):
    # 检查重复项，中文相同，但英文不同
    zhs = {}
    for item in array:
        if item["zh"] == "":
            continue
        zh = item["zh"]
        en = item["en"]
        if zh in zhs and zhs[zh] != en:
            print(f"warning: [{logger}] 发现重复的中文，对应不同的英文", item['zh'])
        else:
            zhs[zh] = en


def check_duplicate_ens(array: list[dict], logger: str):
    # 检查重复项，英文相同，但中文不同
    ens = {}
    for item in array:
        if item["en"] == "":
            continue
        zh = item["zh"]
        en = item["en"]
        if en in ens and ens[en] != zh:
            print(f"warning: [{logger}] 发现重复的英文，对应不同的中文", item['en'])
        else:
            ens[en] = zh


def update_asset_attributes():
    print("info: 更新 assets/attributes.json ...")
    attrs = read_json(at("assets/attributes.json"))
    update_required(attrs, "ClientStrings,Id,Text",  # type: ignore
                    "attributes")
    with open(at("assets/attributes.json"), "w", encoding="utf-8") as f:
        json.dump(attrs, f, ensure_ascii=False, indent=2)


def update_asset_properties():
    print("info: 更新 assets/properties.json ...")
    props = read_json(at("assets/properties.json"))
    update_required(props, "ClientStrings,Id,Text",  # type: ignore
                    "properties")
    with open(at("assets/properties.json"), "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    # 首饰的品质类型也属于properties，但单独成表
    print("info: 创建 assets/properties2.json ...")
    qualitytypes = export_all(
        "AlternateQualityTypes,Id,Description")
    with open(at("assets/properties2.json"), "w", encoding="utf-8") as f:
        json.dump(qualitytypes, f, ensure_ascii=False, indent=2)


def update_asset_requirements():
    print("info: 更新 assets/requirements.json ...")
    reqs = read_json(at("assets/requirements.json"))
    update_required(reqs, "ClientStrings,Id,Text",  # type: ignore
                    "requirements")
    with open(at("assets/requirements.json"), "w", encoding="utf-8") as f:
        json.dump(reqs, f, ensure_ascii=False, indent=2)
    print("info: 更新 assets/requirement_suffixes.json ...")
    reqs = read_json(at("assets/requirement_suffixes.json"))
    update_required(reqs, "ClientStrings,Id,Text",  # type: ignore
                    "requirements")
    with open(at("assets/requirement_suffixes.json"), "w", encoding="utf-8") as f:
        json.dump(reqs, f, ensure_ascii=False, indent=2)

# ======== Task: 更新assets/base_types/* =========


# POE2 0.1,0.2中遗产的基底类型
LEGACY_BASE_TYPE_IDS_BEFORE_0_3 = [
    "Metadata/Items/Weapons/TwoHandWeapons/Crossbows/FourCrossbow3Cruel",
    "Metadata/Items/Weapons/OneHandWeapons/OneHandMaces/FourOneHandMace5Cruel",
    "Metadata/Items/Armours/Gloves/FourGlovesInt3Cruel",
    "Metadata/Items/Armours/Focii/FourFocus3Cruel",
]


def create_asset_base_types():
    type_tables = [
        ("weapons", "WeaponTypes"),
    ]

    item_class_ids = [
        # name,itemClassIds
        ("helmets", ["Helmet"]),
        ("body_armours", ["Body Armour"]),
        ("gloves", ["Gloves"]),
        ("boots", ["Boots"]),
        ("amulets", ["Amulet"]),
        ("belts", ["Belt"]),
        ("shields", ["Shield", "Buckler", "Focus"]),
        ("flasks", ["LifeFlask", "ManaFlask", "UtilityFlask"]),
        ("jewels", ["Jewel"]),
        ("quivers", ["Quiver"]),
        ("rings", ["Ring"]),
        ("soul_cores", ["SoulCore"]),
        ("gems", ["Active Skill Gem", "Meta Skill Gem", "Support Skill Gem"])
    ]
    equipment_names = ["helmets", "body_armours", "gloves", "boots", "amulets", "belts", "shields",
                       "flasks", "jewels", "quivers", "rings"]

    def get_by_type_table(table_name):
        table1 = (TX, CHS, table_name)
        table2 = (TX, CHS, "BaseItemTypes")
        table3 = (GGG, EN, "BaseItemTypes")

        load_table(*table1)
        load_table(*table2)
        load_table(*table3)

        duck_name1 = duck_table_name(*table1)
        duck_name2 = duck_table_name(*table2)
        duck_name3 = duck_table_name(*table3)
        rows = duckdb.sql(f"""SELECT {duck_name2}.Id, {duck_name2}.Name, {duck_name3}.Name, {duck_name2}.DropLevel FROM {duck_name2},{duck_name3}
                WHERE {duck_name2}._index in (
                    SELECT BaseItemType FROM {duck_name1}
                ) AND {duck_name2}.Id = {duck_name3}.Id
            """).fetchall()

        array = [{"id": r[0], "zh": r[1], "en": r[2], "dropLevel": r[3]}
                 for r in rows]

        return array

    def get_by_item_class_ids(item_class_ids):
        table1 = (TX, CHS, "ItemClasses")
        table2 = (TX, CHS, "BaseItemTypes")
        table3 = (GGG, EN, "BaseItemTypes")
        load_table(*table1)
        load_table(*table2)
        load_table(*table3)
        duck_name1 = duck_table_name(*table1)
        duck_name2 = duck_table_name(*table2)
        duck_name3 = duck_table_name(*table3)

        array = []

        for item_class_id in item_class_ids:
            rows = duckdb.sql(f"""SELECT {duck_name2}.Id, {duck_name2}.Name, {duck_name3}.Name, {duck_name2}.DropLevel FROM {duck_name2},{duck_name3}
                    WHERE {duck_name2}.ItemClass == (
                        SELECT _index FROM {duck_name1} WHERE Id == '{item_class_id}'
                    ) AND {duck_name2}.Id = {duck_name3}.Id
                """).fetchall()

            array.extend(
                [{"id": r[0], "zh": r[1], "en": r[2], "dropLevel": r[3]} for r in rows])
        return array

    equipment_base_types = []

    for entry in type_tables:
        name, table_name = entry
        array = get_by_type_table(table_name)
        array = [item for item in array if item["id"]
                 not in LEGACY_BASE_TYPE_IDS_BEFORE_0_3]
        print(f"info: 创建 assets/poe2/base_types/{name}.json")
        save_json(at(f"assets/poe2/base_types/{name}.json"), array)

        equipment_base_types.extend(array)

    for entry in item_class_ids:
        name, item_class_ids = entry
        array = get_by_item_class_ids(item_class_ids)
        array = [item for item in array if item["id"]
                 not in LEGACY_BASE_TYPE_IDS_BEFORE_0_3]
        print(f"info: 创建 assets/poe2/base_types/{name}.json")
        save_json(at(f"assets/poe2/base_types/{name}.json"), array)

        if name in equipment_names:
            equipment_base_types.extend(array)
        else:
            check_duplicate_zhs(array, f"base_types/{name}")

    check_duplicate_zhs(equipment_base_types, "basetypes/equipments")


# ======== Task: 创建assets/passive_skills/* ===========


def create_asset_passive_skills():
    table1 = (TX, CHS, "PassiveSkills")
    table2 = (GGG, EN, "PassiveSkills")
    load_table(*table1)
    load_table(*table2)
    duck_name1 = duck_table_name(*table1)
    duck_name2 = duck_table_name(*table2)

    rows = duckdb.sql(f"""SELECT {duck_name1}.Id, {duck_name1}.Name, {duck_name2}.Name
        FROM {duck_name1}
        LEFT JOIN {duck_name2} on {duck_name1}.Id = {duck_name2}.Id
        WHERE {duck_name1}.IsKeystone == 1
    """).fetchall()

    array = [{"id": r[0], "zh": r[1], "en": r[2]} for r in rows]
    print(f"info: 创建 assets/poe2/passive_skills/keystones.json")
    save_json(at(f"assets/poe2/passive_skills/keystones.json"), array)
    check_duplicate_zhs(array, "passive_skills/keystones")

    rows = duckdb.sql(f"""SELECT {duck_name1}.Id, {duck_name1}.Name, {duck_name2}.Name
        FROM {duck_name1}
        LEFT JOIN {duck_name2} on {duck_name1}.Id = {duck_name2}.Id
        WHERE {duck_name1}.IsNotable == 1
    """).fetchall()

    array = [{"id": r[0], "zh": r[1], "en": r[2]} for r in rows]
    print(f"info: 创建 assets/poe2/passive_skills/notables.json")
    save_json(at(f"assets/poe2/passive_skills/notables.json"), array)
    check_duplicate_zhs(array, "passive_skills/notables")

# ======== Task: 更新assets/uniques.json ===================


# POE2 0.1,0.2中遗产的基底类型
LEGACY_UNIQUE_BEFORE_0_3 = [
    "Demigod's Virtue",
    "Bluetongue",
    "INCOMPLETE",
    "Redbeak",
    "The Dancing Dervish",
    "Winter's Bite"
]


def export_unique_names():
    """根据UniqueStashLayout表，从Words表中导出传奇名称"""
    table1 = (GGG, EN, "UniqueStashLayout")
    table2 = (TX, CHS, "Words")
    table3 = (GGG, EN, "Words")

    load_table(*table1)
    load_table(*table2)
    load_table(*table3)

    duck_name1 = duck_table_name(*table1)
    duck_name2 = duck_table_name(*table2)
    duck_name3 = duck_table_name(*table3)
    rows = duckdb.sql(f"""SELECT {duck_name2}.Text, {duck_name2}.Text2, {duck_name3}.Text2 FROM {duck_name2},{duck_name3}
            WHERE {duck_name2}._index in (
                SELECT WordsKey FROM {duck_name1}
            ) AND {duck_name2}.Text = {duck_name3}.Text
        """).fetchall()
    return [{"id": r[0], "zh": r[1], "en": r[2]} for r in rows]


def init_uniques_by_trade_site():
    unique_names = export_unique_names()
    check_duplicate_ens(unique_names, "unique names")
    unique_names_en_idx = {u["en"]: u for u in unique_names}

    types = export_all("BaseItemTypes,Id,Name")
    check_duplicate_ens(types, "base types")
    types_en_idx = {t["en"]: t for t in types}

    trade_items = read_json(at("export/trade/global/items.json"))
    array = []
    for category in trade_items["result"]:
        if "id" not in category or category["id"] not in ITEMS_EQUIPEMNT_IDS:
            continue
        entries = category["entries"]
        for entry in entries:
            if "flags" not in entry or "unique" not in entry["flags"] or not entry["flags"]["unique"]:
                continue
            if entry["name"] in LEGACY_UNIQUE_BEFORE_0_3:
                continue
            item = {"id": 0, "zh": "", "en": entry["name"],
                    "typeId": 0, "zhType": "", "enType": entry["type"]}
            if entry["name"] in unique_names_en_idx:
                u = unique_names_en_idx[entry["name"]]
                item["zh"] = u["zh"]
                item["id"] = u["id"]
            else:
                print("warning: [uniques] 未找到传奇物品的中文名", entry["name"])
            if entry["type"] in types_en_idx:
                t = types_en_idx[entry["type"]]
                item["zhType"] = t["zh"]
                item["typeId"] = t["id"]
            else:
                print("warning: [uniques] 警告，未找到传奇物品的中文类型名", entry["type"])
            array.append(item)

    save_json(at("assets/poe2/uniques.json"), array)


def update_uniques_inner(array: list):
    dat_unique_names = export_unique_names()
    data_unique_names_zh_idx = {u["zh"]: u for u in dat_unique_names}
    new_uniques_names = {item["zh"]
                         for item in dat_unique_names}-{item["zh"] for item in array}
    for name in new_uniques_names:
        print("info: [uniques] 发现新的暗金：", name)
        u = data_unique_names_zh_idx[name]
        array.append({"id": u["id"], "zh": name, "en": u["en"],
                     "typeId": "", "zhType": "", "enType": ""})

    update_required(array, "Words,Text,Text2", "uniques name")

    ggg_trade_uniques = export_trade_uniques(GGG)
    ggg_trade_uniques_name_idx = {}
    for u in ggg_trade_uniques:
        name = u["name"]
        if name not in ggg_trade_uniques_name_idx:
            ggg_trade_uniques_name_idx[name] = []
        ggg_trade_uniques_name_idx[name].append(u)
    for u in array:
        if not u["enType"]:
            if u["en"] in ggg_trade_uniques_name_idx:
                matches = ggg_trade_uniques_name_idx[u["en"]]
                if len(matches) > 1:
                    print("warning: [uniques] 在交易数据发现重复的英文传奇名称，对应不同的基底类型",
                          u["en"], matches[0]["type"], matches[1]["type"], "...")
                else:
                    u["enType"] = matches[0]["type"]

    update_required(array, "BaseItemTypes,Id,Name",
                    "uniques type", "typeId,zhType,enType")


def update_uniques():
    """
    更新暗金数据。当游戏更新时，需要实现：
    1. 根据dat数据，自动添加新的暗金(id,zh,en)，有时也可能是手动添加(只添加zh)
    2. 如果是手动添加，关联Words表（更新id），并更新en
    3. 根据trade数据，添加zhType
    4. 根据zhType，关联BaseItemType表
    5. 更新enType
    6. 根据id,typeId，更新所有数据

    """
    uniques = read_json(at("assets/poe2/uniques.json"))
    update_uniques_inner(uniques)
    save_json(at("assets/poe2/uniques.json"), uniques)

# ======== Task: 创建assets/tables/words,mods =========


def create_asset_words():
    table1 = (TX, CHS, "Words")
    table2 = (GGG, EN, "Words")
    pkey_name = "Text"
    field_name = "Text2"

    load_table(*table1)
    load_table(*table2)

    duck_name1 = duck_table_name(*table1)
    duck_name2 = duck_table_name(*table2)

    rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name},{duck_name1}.{field_name},{duck_name2}.{field_name},{duck_name1}.Wordlist
        FROM {duck_name1}
        LEFT JOIN {duck_name2} ON {duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}""").fetchall()

    array = [{"id": row[0], "zh": row[1], "en": row[2]}
             for row in rows if row[3] in [2, 3]]
    print("info: 创建 assets/poe2/tables/Words.json ...")
    save_json(at("assets/poe2/tables/Words.json"), array)


def create_asset_mods():
    array = export_all("Mods,Id,Name")
    check_duplicate_zhs(array, "mods")

    print("创建 assets/poe2/tables/Mods.json ...")
    save_json(at("assets/poe2/tables/Mods.json"), array)

# ======== Task: 更新assets/stat_descs/stats.json ========


def stat_desc_path(client: str, desc: str) -> str:
    '''获取词缀描述文件路径'''
    return at("export/game", client, 'files', f"Metadata@StatDescriptions@{desc}.csd")


def read_stat_desc(client: str, desc: str) -> list[str]:
    '''读取词缀描述文件'''
    file = stat_desc_path(client, desc)
    # UTF16-LE-BOM
    with open(file, 'rt', encoding='utf-16') as f:
        content = f.read()
        lines = content.splitlines()
        return lines


class Prop:
    def __init__(self) -> None:
        self.name = ""
        self.param_id = -1  # 参数索引，-1表示属性对应Text


class Param:
    def __init__(self) -> None:
        self.matcher: str = ""
        self.Props: set[str] = set()


class Text:
    def __init__(self) -> None:
        self.params: list[Param] = []
        self.template: str = ""
        self.props: set[str] = set()


class Desc:
    def __init__(self) -> None:
        self.id = ""
        self.stat_ids = []
        self.texts: dict[str, list[Text]] = {}  # 根据语言索引的的文本列表


# 1: 已读取"description"
# 2: 已读取语言行
# 3: 已读取Texts行数
# 4: 已读完Texts
# 10: 遇到无效行
STATE_TAG_READED = 1
STATE_LANG_READED = 2
STAT_TEXTS_COUNT_READED = 3
STATE_TEXTS_READED = 4
STATE_ERROR = 10


class DescParser:
    def __init__(self) -> None:
        self.descs = []
        self.state: int = STATE_TEXTS_READED
        self.curr_desc = Desc()
        self.curr_lang = ""
        self.curr_text_count = 0

    def parse(self, lines: list[str]) -> list[Desc]:
        for (i, line) in enumerate(lines):
            line = line.strip()
            if line == "" or line.startswith("no_description") or line.startswith("include"):
                continue
            match self.state:
                case 1:
                    self.curr_desc.stat_ids = self.parse_id_line(line)
                    self.curr_desc.id = " ".join(self.curr_desc.stat_ids)
                    self.curr_lang = EN
                    self.curr_desc.texts[self.curr_lang] = []
                    self.state = STATE_LANG_READED  # 英文没有语言行，读完id行直接设置语言并跳转到STATE_LANG_READED
                case 2:
                    if line.isnumeric():
                        self.curr_text_count = int(line)
                        self.state = STAT_TEXTS_COUNT_READED
                    else:
                        self.state = 10
                case 3:
                    text = self.parse_text(line)
                    self.curr_desc.texts[self.curr_lang].append(text)
                    self.curr_text_count -= 1
                    if self.curr_text_count == 0:
                        self.state = STATE_TEXTS_READED
                case 4:
                    if self.is_tag_line(line):
                        self.curr_desc = Desc()
                        self.descs.append(self.curr_desc)
                        self.state = STATE_TAG_READED
                    elif self.is_lang_line(line):
                        self.curr_lang = self.parse_lang(line)
                        self.curr_desc.texts[self.curr_lang] = []
                        self.state = STATE_LANG_READED
                    else:
                        self.state = STATE_ERROR
                case 10:
                    raise Exception(f"error: [stat desc] 无效行 {line}")

        return self.descs

    def is_tag_line(self, line: str) -> bool:
        return line == "description"

    def is_lang_line(self, line: str) -> bool:
        return line.startswith("lang ")

    def parse_id_line(self, line: str) -> list[str]:
        m = re.match(r"^(\d)\s+(.+)$", line)
        if m:
            return [id.strip() for id in m[2].strip().split(" ")]
        else:
            raise Exception(f"error: [stat desc] 错误的Id行 {line}")

    def parse_lang(self, line: str) -> str:
        m = re.match(r'^lang\s+"(.+)"$', line)
        if m:
            return m[1]
        else:
            raise Exception(f"error: [stat desc] 错误的语言行 {line}")

    def parse_text(self, line: str) -> Text:
        text = Text()
        m = re.match(r'^(.+)\s"(.*?)"(.*)$', line)
        if m is None:
            raise Exception(f"error [stat desc] 错误的Text行 {line}")

        params_str, tmpl_str, props_str = m[1].strip(), m[2], m[3].strip()

        for matcher_str in re.split(r"\s+", params_str):
            if matcher_str == "":
                continue
            if matcher_str == "#" or "|" in matcher_str or is_number(matcher_str) or matcher_str.startswith("!"):
                param = Param()
                param.matcher = matcher_str
                text.params.append(param)
            else:
                text.props.add(matcher_str)

        text.template = self.format_template(tmpl_str)

        props = self.parse_props(props_str)
        for prop in props:
            if prop.param_id >= 0:
                text.params[prop.param_id].Props.add(prop.name)

            else:
                text.props.add(prop.name)

        return text

    def format_template(self, tmpl: str) -> str:
        # 将`\n`字符串替换为换行符
        tmpl = tmpl.replace(r"\n", "\n")

        # 将自动编号替换为显式编号
        r1 = re.compile(r"{(:[^}]+)?}")
        r2 = re.compile(r"{(\d+)(:[^}]+)?}")
        if r1.match(tmpl) and r2.match(tmpl):
            print("warning: [stat desc] 模板中同时存在自动编号和显式编号，可能导致错误", tmpl)
            return tmpl

        n = 0

        def replace(match):
            nonlocal n
            replacement = f"{{{n}{match.group(1) if match.group(1) else ''}}}"
            n += 1
            return replacement

        return re.sub(r1, replace, tmpl)

    def parse_props(self, props_str: str) -> list[Prop]:
        props: list[Prop] = []

        if props_str == "":
            return props

        on_prop = False
        for token in re.split(r"\s+", props_str):
            if token.isnumeric():
                if on_prop:
                    props[-1].param_id = int(token)-1
                else:
                    raise Exception(
                        f"error [stat desc] 解析文本属性错误，预期属性名，而非属性索引 {props_str}")
            else:
                prop = Prop()
                prop.name = token
                props.append(prop)
                on_prop = True

        return props


def merge_descs_ggg_to_tx(tx_descs: list[Desc], ggg_descs: list[Desc]) -> list[Desc]:
    ggg_idx = {desc.id: desc for desc in ggg_descs}
    for desc in tx_descs:
        desc.texts[EN] = ggg_idx[desc.id].texts[EN]
        if CHS not in desc.texts:
            continue
        if len(desc.texts[EN])!= len(desc.texts[CHS]):
            print("warning: [stat desc] 中英文文本数量不匹配", desc.id)
    return tx_descs


def create_asset_stat_descs():
    print("info: [stat] 创建 assets/stat_descs/stats.json ...")
    tx_content = read_stat_desc(TX, "stat_descriptions")
    ggg_content = read_stat_desc(GGG, "stat_descriptions")

    tx_descs = DescParser().parse(tx_content)
    ggg_descs = DescParser().parse(ggg_content)

    descs = merge_descs_ggg_to_tx(tx_descs, ggg_descs)

    array = []
    for desc in descs:
        entry = {
            "id": desc.id,
            "texts": {}
        }
        for lang in desc.texts:
            if lang not in [CHS, EN]:
                continue
            entry["texts"][lang] = []
            for text in desc.texts[lang]:
                text_entry = {
                    "params": [],
                    "template": text.template
                }
                if len(text.props) > 0:
                    text_entry["props"] = list(text.props)

                for param in text.params:
                    param_entry = {
                        "matcher": param.matcher
                    }
                    if len(param.Props) > 0:
                        param_entry["props"] = list(  # type: ignore
                            param.Props)

                    text_entry["params"].append(param_entry)
                entry["texts"][lang].append(text_entry)
        array.append(entry)

    saved = at("assets/poe2/stat_descs/stats.json")
    must_parent(saved)
    with open(saved, "w", encoding="utf-8") as f:
        json.dump(array, f, ensure_ascii=False, indent=2)

# =============================================== CLI


def run_all_tasks():
    # update_asset_attributes()
    # update_asset_properties()
    update_asset_requirements()
    # create_asset_base_types()
    # create_asset_passive_skills()
    # update_uniques()
    # create_asset_words()
    # create_asset_mods()
    # create_asset_stat_descs()


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        run_all_tasks()
