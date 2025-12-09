import json
from typing import Any

import duckdb
from common import CLIENT_GLOBAL, CLIENT_TENCENT, LANG_CHS, LANG_EN, at, read_json, save_json, sql_escape
from export import game

ATTRIBUTES_PATH = "db/attributes.json"
PROPERTIES_PATH = "db/properties.json"
PROPERTIES2_PATH = "db/properties2.json"
REQUIREMENTS_PATH = "db/requirements.json"
REQUIREMENT_SUFFIXES_PATH = "db/requirement_suffixes.json"


def select_pairs(table_info: str, field_info="zh,en,ref_id") -> list:
    '''导出表中的所有内容。table_info采用`表名,主键名,字段名`的格式。'''
    [table_name, pkey_name, field_name] = table_info.split(",")

    table1 = (CLIENT_TENCENT, LANG_CHS, table_name)
    table2 = (CLIENT_GLOBAL, LANG_EN, table_name)

    game.load_table(*table1)
    game.load_table(*table2)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)

    rows = duckdb.sql(f"""SELECT {duck_name1}.{field_name},{duck_name2}.{field_name},{duck_name1}.{pkey_name}
        FROM {duck_name1}
        INNER JOIN {duck_name2} ON {duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}""").fetchall()

    return [{"zh": row[0], "en": row[1], "ref_id": row[2]} for row in rows]


def update_pair(pair: dict, logger: str, table_info: str, field_info: str, join_fields: set, filter: dict[str, Any]):
    '''
    更新键值对，用于更新properties,requirements,attributes的通用函数，包括它们的值。

    每个键值对包括以下键和值：

    - zh 中文内容
    - en 英文内容
    - values(可选) 值序列，每个值是一个键值对（不包含values字段）
    - ref(可选) 关联的表信息，格式为`表名,主键字段,内容字段`
    - ref_id 关联的表中的记录的主键值（实际可能存在重复）

    properties,requirements,attributes包括它们的值主要来源ClientString表。

    更新有两个含义：
    1. 当中文或英文发生改变时，自动更新中文或英文。
    2. 新增项只需要手动添加中文(zh)和ref，自动填充en和ref_id。

    为了保证JSON格式的一致性（字段顺序），当手动添加`zh`和`ref`，添加空的en、values(如果存在)、ref和ref_id。
    '''

    [table_name, pkey_name, field_name] = table_info.split(",")
    [zh_field, en_field, id_field] = field_info.split(",")

    table1 = (CLIENT_TENCENT, LANG_CHS, table_name)
    table2 = (CLIENT_GLOBAL, LANG_EN, table_name)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)

    game.load_table(*table1)
    game.create_index(duck_name1, pkey_name)
    game.create_index(duck_name1, field_name)
    game.load_table(*table2)
    game.create_index(duck_name2, pkey_name)
    game.create_index(duck_name2, field_name)

    join_conds = f"{duck_name1}.{pkey_name} = {duck_name2}.{pkey_name}"
    if len(join_fields) > 0:
        builder = [join_conds]
        for field in join_fields:
            builder.append(
                f"{duck_name1}.{field} = {duck_name2}.{field}")
        join_conds = " AND ".join(builder)

    more_where_conds = "AND 1=1"
    if len(filter) > 0:
        builder = []
        for k, v in filter.items():
            if type(v) is int:
                builder.append(f"{duck_name1}.{k} = {v}")
            elif type(v) is str:
                builder.append(
                    f"{duck_name1}.{k} = '{sql_escape(v)}'")
            else:
                raise Exception(
                    f"error: [{logger}] 不支持的 filter 类型 {type(v)}")
        more_where_conds = "AND "+" AND ".join(builder)

    def add_id(pair):
        if id_field in pair and pair[id_field]:
            return

        # 确保字段存在，避免访问错误
        if zh_field not in pair:
            pair[zh_field] = ""
        if en_field not in pair:
            pair[en_field] = ""

        rows = []

        # 如果中英文都存在，那么两者同时匹配
        if en_field in pair and pair[en_field] and zh_field in pair and pair[zh_field]:
            rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name} FROM {duck_name1}
            INNER JOIN {duck_name2} ON {join_conds}
            WHERE {duck_name1}.{field_name} == '{sql_escape(pair[zh_field])}'
            AND {duck_name2}.{field_name} == '{sql_escape(pair[en_field])}'
            {more_where_conds}""").fetchall()
        elif zh_field in pair and pair[zh_field]:  # 只匹配中文
            rows = duckdb.sql(f"""SELECT {duck_name1}.{pkey_name} FROM {duck_name1}
            WHERE {duck_name1}.{field_name} == '{sql_escape(pair[zh_field])}'
            {more_where_conds}""").fetchall()
        elif en_field in pair and pair[en_field]:  # 只匹配英文
            rows = duckdb.sql(f"""SELECT {duck_name2}.{pkey_name} FROM {duck_name2}
            WHERE {duck_name2}.{field_name} == '{sql_escape(pair[en_field])}' 
            {more_where_conds}""").fetchall()

        if len(rows) > 1:
            print(
                f"warning: [{logger}] {pair['zh']},{pair['en']} 在 {table_name} 表中匹配多个记录 {rows[0][0]}, {rows[1][0]} 等")
        if len(rows) == 1:
            pair[id_field] = rows[0][0]

    def update_text(pair):
        if id_field not in pair or not pair[id_field]:
            return
        id = pair[id_field]
        rows = duckdb.sql(f"""SELECT {duck_name1}.{field_name},{duck_name2}.{field_name} FROM {duck_name1}
        INNER JOIN {duck_name2} ON {join_conds}
        WHERE {duck_name1}.{pkey_name} == '{sql_escape(id)}' 
        {more_where_conds}""")

        if len(rows) > 1:
            print(
                f"warning: [{logger}] {pair['zh']},{pair['en']}在 {table_name} 表中匹配 {len(rows)} 个记录，检查更新失败")
            return

        if len(rows) == 0:
            print(
                f"warning: [{logger}] {pair['zh']},{pair['en']} 在 {table_name} 表中未找到记录，检查更新失败")
            return
        row = rows.fetchone()
        # row必然不为None，这里是为了类型检查方便
        if row:
            if zh_field not in pair:
                pair[zh_field] = ""
            if en_field not in pair:
                pair[en_field] = ""
            if pair[zh_field] != row[0] or pair[en_field] != row[1]:
                old_zh = pair[zh_field]
                old_en = pair[en_field]
                print(
                    f"info: [{logger}] 更新 '{old_zh}','{old_en}'  -> '{row[0]}','{row[1]}'")
                pair[zh_field] = row[0]
                pair[en_field] = row[1]

    def update_values(pair):
        if "values" in pair:
            update_pairs(pair["values"], logger)

    add_id(pair)
    update_text(pair)
    update_values(pair)


def update_pairs(pairs: list[dict], logger: str, table_info="", field_info="zh,en,ref_id", join_fields=set(), filter={}):
    for pair in pairs:
        if table_info == "":
            table_info = pair.get("ref", "")
        if table_info == "":
            continue
        update_pair(pair, logger, table_info,
                    field_info=field_info, join_fields=join_fields, filter=filter)


def update_attributes():
    print(f"info: 更新 {ATTRIBUTES_PATH} ...")
    attrs = read_json(at(ATTRIBUTES_PATH))
    update_pairs(attrs, "db/attributes")
    save_json(at(ATTRIBUTES_PATH), attrs)


def update_properties():
    print(f"info: 更新 {PROPERTIES_PATH} ...")
    props = read_json(at(PROPERTIES_PATH))
    update_pairs(props, "db/properties")
    save_json(at(PROPERTIES_PATH), props)

    # 首饰的品质类型也属于properties，不需要数据清洗，直接导出所有
    print(f"info: 创建 {PROPERTIES2_PATH} ...")
    qualitytypes = select_pairs(
        "AlternateQualityTypes,Id,Description")
    save_json(at(PROPERTIES2_PATH), qualitytypes)


def update_requirements():
    print(f"info: 更新 {REQUIREMENTS_PATH} ...")
    reqs = read_json(at(REQUIREMENTS_PATH))
    update_pairs(reqs, "db/requirements")
    save_json(at(REQUIREMENTS_PATH), reqs)
    print(f"info: 更新 {REQUIREMENT_SUFFIXES_PATH} ...")
    reqs = read_json(at(REQUIREMENT_SUFFIXES_PATH))
    update_pairs(reqs, "db/requirements_suffixes")
    save_json(at(REQUIREMENT_SUFFIXES_PATH), reqs)
