import duckdb
from common import CLIENT_GLOBAL, CLIENT_TENCENT, LANG_CHS, LANG_EN, at, read_json, save_json
from export import game


TATTOOS_PATH = "db/items/tattoos.json"


def check_duplicate_zhs(array: list[dict], logger: str):
    """检查重复的中文，但英文不同"""
    zhs = {}
    for item in array:
        if item["zh"] == "":
            continue
        zh = item["zh"]
        en = item["en"]
        if zh in zhs and zhs[zh] != en:
            print(f"warning: [{logger}] 发现重复的中文，但英文不同", item['zh'])
        else:
            zhs[zh] = en


def remove_duplicate(array: list[dict]) -> list[dict]:
    """移除重复的键值对，保留第一个出现的项"""
    seen = set()
    unique_array = []
    for item in array:
        zh = item["zh"]
        en = item["en"]
        zh_en = f"{zh}|{en}"
        if zh_en not in seen:
            seen.add(zh_en)
            unique_array.append(item)
    return unique_array


"""腾讯服之前遗产的基底类型"""
LEGACY_BASE_TYPE_IDS_BEFORE_TENCENT = [
    "Metadata/Items/Quivers/Quiver4"  # 存在同中文名物品，移除以避免名称冲突
]


def get_by_type_table(table_name):
    table1 = (CLIENT_TENCENT, LANG_CHS, table_name)
    table2 = (CLIENT_TENCENT, LANG_CHS, "BaseItemTypes")
    table3 = (CLIENT_GLOBAL, LANG_EN, "BaseItemTypes")

    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)

    rows = duckdb.sql(f"""SELECT {duck_name2}.Name, {duck_name3}.Name, {duck_name2}.Id FROM {duck_name2},{duck_name3}
                WHERE {duck_name2}._index in (
                    SELECT BaseItemTypesKey FROM {duck_name1}
                ) AND {duck_name2}.Id = {duck_name3}.Id
                ORDER BY {duck_name2}.DropLevel DESC
            """).fetchall()

    array = [{"zh": r[0], "en": r[1], "ref_id": r[2]}
             for r in rows]

    return remove_duplicate(array)


def get_by_item_class_ids(item_class_ids):
    table1 = (CLIENT_TENCENT, LANG_CHS, "ItemClasses")
    table2 = (CLIENT_TENCENT, LANG_CHS, "BaseItemTypes")
    table3 = (CLIENT_GLOBAL, LANG_EN, "BaseItemTypes")
    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)
    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)

    array = []

    for item_class_id in item_class_ids:
        rows = duckdb.sql(f"""SELECT {duck_name2}.Name, {duck_name3}.Name,{duck_name2}.Id FROM {duck_name2},{duck_name3}
                    WHERE {duck_name2}.ItemClassesKey == (
                        SELECT _index FROM {duck_name1} WHERE Id == '{item_class_id}'
                    ) AND {duck_name2}.Id = {duck_name3}.Id
                    ORDER BY {duck_name2}.DropLevel DESC
                """).fetchall()

        array.extend(
            [{"zh": r[0], "en": r[1], "ref_id": r[2]} for r in rows])

    return remove_duplicate(array)


def create_equipments():
    type_tables = [
        ("weapons", "WeaponTypes"),
    ]

    item_class_ids = [
        # name,itemClassIds
        ("amulets", ["Amulet"]),
        ("belts", ["Belt"]),
        ("body_armours", ["Body Armour"]),
        ("boots", ["Boots"]),
        ("flasks", ["LifeFlask", "ManaFlask", "HybridFlask", "UtilityFlask"]),
        ("gloves", ["Gloves"]),
        ("grafts", ["BrequelGraft"]),
        ("helmets", ["Helmet"]),
        ("jewels", ["Jewel", "AbyssJewel"]),
        ("quivers", ["Quiver"]),
        ("rings", ["Ring"]),
        ("shields", ["Shield"]),
        ("tinctures", ["Tincture"])
    ]
    equipment_names = ["helmets", "body_armours", "gloves", "boots", "amulets", "belts", "shields",
                       "flasks", "jewels", "quivers", "rings"]

    equipment_base_types = []

    for entry in type_tables:
        name, table_name = entry
        print(f"info: 创建 db/items/{name}.json...")

        array = get_by_type_table(table_name)
        array = [item for item in array if item["ref_id"]
                 not in LEGACY_BASE_TYPE_IDS_BEFORE_TENCENT]
        save_json(at(f"db/items/{name}.json"), array)

        equipment_base_types.extend(array)

    for entry in item_class_ids:
        name, item_class_ids = entry
        print(f"info: 创建 db/items/{name}.json...")

        array = get_by_item_class_ids(item_class_ids)
        array = [item for item in array if item["ref_id"]
                 not in LEGACY_BASE_TYPE_IDS_BEFORE_TENCENT]
        save_json(at(f"db/items/{name}.json"), array)

        if name in equipment_names:
            equipment_base_types.extend(array)
        else:
            check_duplicate_zhs(array, f"items/{name}")

    check_duplicate_zhs(equipment_base_types, "items/equipments")


def create_tattoos():
    print(f"info: 创建 {TATTOOS_PATH}...")

    table1 = (CLIENT_TENCENT, LANG_CHS, "PassiveSkillTattoos")
    table2 = (CLIENT_TENCENT, LANG_CHS, "BaseItemTypes")
    table3 = (CLIENT_GLOBAL, LANG_EN, "BaseItemTypes")
    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)
    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)
    game.create_index(duck_name1, "Tattoo")
    game.create_index(duck_name2, "_index")
    game.create_index(duck_name2, "Id")
    game.create_index(duck_name3, "Id")

    rows = duckdb.sql(f"""SELECT {duck_name2}.Name, {duck_name3}.Name, {duck_name2}.Id FROM {duck_name1}
            INNER JOIN {duck_name2} ON {duck_name1}.Tattoo = {duck_name2}._index
            INNER JOIN {duck_name3} ON {duck_name2}.Id = {duck_name3}.Id
            ORDER BY {duck_name2}._index
        """).fetchall()

    array = [{"zh": r[0], "en": r[1], "ref_id": r[2]}
             for r in rows if not r[1].startswith("[DNT - UNUSED]")]
    array = remove_duplicate(array)

    save_json(at(TATTOOS_PATH), array)


def create_items():
    create_equipments()
    create_tattoos()
