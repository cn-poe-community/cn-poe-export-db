import json
import os

from common import at, must_parent, read_json, read_ndjson
from db import gem, pair, passiveskill, stat, unique

ASSETS_PATH = "libs/js/src/assets.ts"

checked_non_ascii_types = {"Maelström Staff"}
checked_non_ascii_names = {"Doppelgänger Guise", "Mjölner"}


def check_non_ascii_names():
    non_ascii_types = set()
    non_ascii_names = set()

    for file_name in os.listdir(at("db/items")):
        source = at("db/items", file_name)
        if os.path.isfile(source) and file_name.endswith(".json"):
            data = read_json(source)
            for item in data:
                basetype = item["en"]
                if not basetype.isascii():
                    non_ascii_types.add(basetype)
                if "uniques" in item:
                    for u in item["uniques"]:
                        name = u["en"]
                        if not name.isascii():
                            non_ascii_names.add(name)

    deprecated_types = checked_non_ascii_types-non_ascii_types
    deprecated_names = checked_non_ascii_names-non_ascii_names
    new_types = non_ascii_types-checked_non_ascii_types
    new_names = non_ascii_names-checked_non_ascii_names

    if len(deprecated_types) != 0:
        print(f"warning: deprecated non-ascii basetypes: {deprecated_types}")
    if len(deprecated_names) != 0:
        print(f"warning: deprecated non-ascii uniques: {deprecated_names}")
    if len(new_types) != 0:
        print(f"warning: new non-ascii basetypes: {new_types}")
    if len(new_names) != 0:
        print(f"warning: new non-ascii uniques: {new_names}")


def snake_to_camel(name: str):
    result = ''
    capitalize_next = False
    for char in name:
        if char == '_':
            capitalize_next = True
        else:
            if capitalize_next:
                result += char.upper()
                capitalize_next = False
            else:
                result += char
    return result


def remain_fields(obj: dict, fields: set[str]):
    keys = list(obj.keys())
    for key in keys:
        if key not in fields:
            del obj[key]
        else:
            val = obj[key]
            if type(val) is dict:
                remain_fields(val, fields)
            elif type(val) is list:
                for item in val:
                    if type(item) is dict:
                        remain_fields(item, fields)


def json_to_js(data, remained_fields, name) -> str:
    for item in data:
        remain_fields(item, remained_fields)
    return f"export const {name} = {json.dumps(data, ensure_ascii=False, indent=2)};"


def jsons_to_js(files: list[str], remained_fields: set, variable_name) -> str:
    data = []
    for file in files:
        data.extend(read_json(file))
    return json_to_js(data, remained_fields, variable_name)


def make_attributes():
    return jsons_to_js([at("db/attributes.json")], {"zh", "en", "values"}, "attributes")


def make_properties():
    return jsons_to_js([at("db/properties.json"), at("db/properties2.json")], {"zh", "en", "values"}, "properties")


def make_requirement():
    codes = []
    codes.append(jsons_to_js(
        [at(pair.REQUIREMENTS_PATH)], {"zh", "en", "values"}, "requirements"))
    codes.append(jsons_to_js(
        [at(pair.REQUIREMENT_SUFFIXES_PATH)], {"zh", "en", "values"}, "requirementSuffixes"))
    return "\n".join(codes)


def make_items():
    uniques = read_ndjson(at(unique.UNIQUES_PATH))
    uniques_base_type_idx = {}
    for u in uniques:
        base_type = u["baseType"]
        if base_type not in uniques_base_type_idx:
            uniques_base_type_idx[base_type] = []
        uniques_base_type_idx[base_type].append(u)

    codes = []
    for file_name in os.listdir(at("db/items")):
        source = at("db/items", file_name)
        if os.path.isfile(source) and file_name.endswith(".json"):
            data = read_json(source)
            for item in data:
                base_type = item["en"]
                if base_type in uniques_base_type_idx:
                    item["uniques"] = uniques_base_type_idx[base_type]
            name = file_name[:-5]
            code = json_to_js(
                data, {"zh", "en", "uniques"}, snake_to_camel(name))
            codes.append(code)
    return "\n".join(codes)


def make_gems():
    codes = []
    codes.append(jsons_to_js(
        [at(gem.SKILL_GEMS_PATH), at(gem.TRANSFIGURED_GEMS_PATH)], {"zh", "en"}, "gems"))
    codes.append(jsons_to_js(
        [at(gem.HYBRID_SKILLS_PATH)], {"zh", "en"}, "hybridSkills"))
    return "\n".join(codes)


def make_passive_skills():
    codes = []
    codes.append(jsons_to_js(
        [at(passiveskill.NOTABLES_PATH)], {"id", "zh", "en"}, "notables"))
    codes.append(jsons_to_js(
        [at(passiveskill.KEYSTONES_PATH)], {"id", "zh", "en"}, "keystones"))
    codes.append(jsons_to_js(
        [at(passiveskill.ASCENDANT_PATH)], {"id", "zh", "en"}, "ascendant"))
    return "\n".join(codes)


def remove_repeats(stats):
    stat_list = []
    stat_map = {}
    for stat in stats:
        zh = stat["zh"]
        en = stat["en"]
        if zh in stat_map:
            old_en = stat_map[zh]["en"]
            if en.casefold() != old_en.casefold():
                print("warning: same zh but diff en")
                print(f"{zh}")
                print(f"{old_en}")  # old
                print(f"{en}")  # old
            continue
        stat_list.append(stat)
        stat_map[zh] = stat
    return stat_list


def make_stats():
    stats = []
    stats.extend(read_json(at(stat.DESC_STATS_PATH)))
    stats.extend(read_json(at(stat.TRADE_STATS_PATH)))

    stats = remove_repeats(stats)

    return json_to_js(stats, {"zh", "en"}, "stats")


def make():
    print("info: [build] making...")
    codes = [
        make_attributes(),
        make_properties(),
        make_requirement(),
        make_items(),
        make_gems(),
        make_passive_skills(),
        make_stats(),
    ]

    must_parent(at(ASSETS_PATH))
    print(f"saved {at(ASSETS_PATH)}")
    with open(at(ASSETS_PATH), 'wt', encoding="utf-8", newline="\n") as f:
        f.write("\n".join(codes))
