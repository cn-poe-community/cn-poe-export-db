import duckdb
from common import CLIENT_GLOBAL, CLIENT_TENCENT, LANG_CHS, LANG_EN, at, read_json, save_json
from db import item
from export import game

SKILL_GEMS_PATH = "db/gems/skill_gems.json"
HYBRID_SKILLS_PATH = "db/gems/hybrid_skills.json"
TRANSFIGURED_GEMS_PATH = "db/gems/transfigured_gems.json"


def get_skill_gems():
    table1 = (CLIENT_TENCENT, LANG_CHS, "SkillGems")
    table2 = (CLIENT_TENCENT, LANG_CHS, "BaseItemTypes")
    table3 = (CLIENT_GLOBAL, LANG_EN, "BaseItemTypes")

    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)

    game.create_index(duck_name2, "_index")
    game.create_index(duck_name2, "Id")
    game.create_index(duck_name3, "Id")

    rows = duckdb.sql(f"""SELECT {duck_name2}.Name, {duck_name3}.Name FROM {duck_name1}
            INNER JOIN {duck_name2} ON {duck_name1}.BaseItemTypesKey = {duck_name2}._index
            INNER JOIN {duck_name3} ON {duck_name2}.Id = {duck_name3}.Id
        """).fetchall()

    array = [{"zh": r[0], "en": r[1]} for r in rows if not r[1].startswith(
        "[UNUSED]") and not r[1].startswith("[DNT]")]

    # 存在同名的数据
    return item.remove_duplicate(array)


def get_transfigured_gems(skill_gem_zh_set: set):
    table1 = (CLIENT_TENCENT, LANG_CHS, "SkillGems")
    table2 = (CLIENT_TENCENT, LANG_CHS, "GemEffects")
    table3 = (CLIENT_GLOBAL, LANG_EN, "GemEffects")

    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)

    game.create_index(duck_name2, "_index")
    game.create_index(duck_name2, "Id")
    game.create_index(duck_name3, "Id")

    def select_gem_effect(index: int) -> tuple | None:
        return duckdb.sql(f"""SELECT {duck_name2}.Name, {duck_name3}.Name FROM {duck_name2}
            INNER JOIN {duck_name3} ON {duck_name2}.Id = {duck_name3}.Id
            WHERE {duck_name2}._index = {index}
        """).fetchone()

    array = []

    rows = duckdb.sql(
        f"""SELECT {duck_name1}.GemEffects FROM {duck_name1}""").fetchall()
    for row in rows:
        effect_indices = row[0]
        for index in effect_indices:
            record = select_gem_effect(index)
            if not record:
                continue
            zh = record[0]
            en = record[1]
            if zh.isascii() or zh in skill_gem_zh_set or "DNT" in en:
                continue

            array.append({"zh": zh, "en": en})

    return item.remove_duplicate(array)


def get_hybrid_support():
    table1 = (CLIENT_TENCENT, LANG_CHS, "SkillGems")
    table2 = (CLIENT_TENCENT, LANG_CHS, "GemEffects")
    table3 = (CLIENT_GLOBAL, LANG_EN, "GemEffects")

    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)

    game.create_index(duck_name2, "_index")

    def select_gem_effect(index: int) -> tuple | None:
        return duckdb.sql(f"""SELECT {duck_name2}.SupportName, {duck_name3}.SupportName FROM {duck_name2}
            INNER JOIN {duck_name3} ON {duck_name2}.Id = {duck_name3}.Id
            WHERE {duck_name2}._index = {index}
        """).fetchone()

    array = []

    rows = duckdb.sql(
        f"""SELECT {duck_name1}.GemEffects FROM {duck_name1}""").fetchall()
    for row in rows:
        effect_indices = row[0]
        for index in effect_indices:
            record = select_gem_effect(index)
            if not record:
                continue
            zh = record[0]
            en = record[1]
            if zh.isascii():
                continue

            array.append({"zh": zh, "en": en})

    return item.remove_duplicate(array)


def get_hybrid_effects(skill_gem_zh_set: set, transfigured_gem_zh_set: set):
    table1 = (CLIENT_TENCENT, LANG_CHS, "SkillGems")
    table2 = (CLIENT_TENCENT, LANG_CHS, "GemEffects")
    table3 = (CLIENT_TENCENT, LANG_CHS, "GrantedEffects")
    table4 = (CLIENT_TENCENT, LANG_CHS, "ActiveSkills")
    table5 = (CLIENT_GLOBAL, LANG_EN, "ActiveSkills")

    game.load_table(*table1)
    game.load_table(*table2)
    game.load_table(*table3)
    game.load_table(*table4)
    game.load_table(*table5)

    duck_name1 = game.duck_table_name(*table1)
    duck_name2 = game.duck_table_name(*table2)
    duck_name3 = game.duck_table_name(*table3)
    duck_name4 = game.duck_table_name(*table4)
    duck_name5 = game.duck_table_name(*table5)

    def select_gem_effect(index: int) -> tuple | None:
        return duckdb.sql(f"""SELECT {duck_name2}.GrantedEffect2 FROM {duck_name2}
            WHERE {duck_name2}._index = {index}
        """).fetchone()

    def select_granted_effect(index: int) -> tuple | None:
        return duckdb.sql(f"""SELECT {duck_name4}.DisplayedName, {duck_name5}.DisplayedName FROM {duck_name3}
            INNER JOIN {duck_name4} ON {duck_name3}.ActiveSkill = {duck_name4}._index
            INNER JOIN {duck_name5} ON {duck_name3}.ActiveSkill = {duck_name5}._index
            WHERE {duck_name3}._index = {index}
        """).fetchone()

    array = []

    rows = duckdb.sql(
        f"""SELECT {duck_name1}.GemEffects FROM {duck_name1}""").fetchall()
    for row in rows:
        effect_indices = row[0]
        for index in effect_indices:
            record = select_gem_effect(index)
            if not record or not record[0]:
                continue
            effect = select_granted_effect(record[0])
            if not effect:
                continue
            zh = effect[0]
            en = effect[1]
            if zh.isascii() or zh in skill_gem_zh_set or zh in transfigured_gem_zh_set:
                continue
            array.append({"zh": zh, "en": en})

    return item.remove_duplicate(array)


def create_gems():
    skill_gems = get_skill_gems()
    skill_gem_zh_set = {g["zh"] for g in skill_gems}

    transfigured_gems = get_transfigured_gems(skill_gem_zh_set)
    transfigured_gem_zh_set = {g["zh"] for g in transfigured_gems}

    hybrid_supports = get_hybrid_support()
    hybrid_effects = get_hybrid_effects(
        skill_gem_zh_set, transfigured_gem_zh_set)

    hybrid_supports.extend(hybrid_effects)

    item.check_duplicate_zhs(skill_gems, SKILL_GEMS_PATH)

    print(f"info: 创建 {SKILL_GEMS_PATH}...")
    save_json(at(SKILL_GEMS_PATH), skill_gems)
    print(f"info: 创建 {TRANSFIGURED_GEMS_PATH}...")
    save_json(at(TRANSFIGURED_GEMS_PATH), transfigured_gems)
    print(f"info: 创建 {HYBRID_SKILLS_PATH}...")
    save_json(at(HYBRID_SKILLS_PATH), hybrid_supports)
