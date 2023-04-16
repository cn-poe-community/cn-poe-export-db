import json
import os
import shutil

src = "src"
dist = "dist/ts"

imports = 'import { Attribute } from "../type/attribute.type";\n\
import { BaseType } from "../type/basetype.type";\n\
import { Gem } from "../type/gem.type";\n\
import { Node } from "../type/passiveskill.type";\n\
import { Property } from "../type/property.type";\n\
import { Requirement, RequirementSuffix } from "../type/requirement.type";\n\
import { Stat } from "../type/stat.type";\n'

types = {}
types["accessories.json"] = "BaseType[]"
types["armour.json"] = "BaseType[]"
types["attributes.json"] = "Attribute[]"
types["flasks.json"] = "BaseType[]"
types["gems.json"] = "Gem[]"
types["jewels.json"] = "BaseType[]"
types["properties.json"] = "Property[]"
types["requirements.json"] = "Requirement[]"
types["requirement_suffixes.json"] = "RequirementSuffix[]"
types["weapons.json"] = "BaseType[]"
types["stats.json"] = "Stat[]"
types["ascendant.json"] = "Node[]"
types["keystones.json"] = "Node[]"
types["notables.json"] = "Node[]"

def emptyDir(dir):
    try:
        shutil.rmtree(dist)
    except:
        print("dist is cleaned")
    os.mkdir(dist, 0o666)

def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data

def json2code(json,variableName, type):
    if variableName == "requirement_suffixes":
        variableName = "requirementSuffixes"
    return f"export const {variableName}: {type} = {json};"

def make_stats():
    stats_folder = os.path.join(src, "stats")
    all_data = []
    for file_name in os.listdir(stats_folder):
        if file_name.endswith(".json"):
            data: list = load_json(os.path.join(stats_folder, file_name))
            all_data.extend(data)
    
    return all_data

def make():
    content = [imports]
    for file_name in os.listdir(src):
        source = os.path.join(src, file_name)
        if os.path.isfile(source) and file_name.endswith(".json"):
            data = load_json(source)
            pure_name = file_name[:-5]
            code = json2code(data, pure_name, types[file_name])
            content.append(code)

    for file_name in os.listdir(os.path.join(src, "passiveskills")):
        source = os.path.join(src, "passiveskills", file_name)
        if os.path.isfile(source) and file_name.endswith(".json"):
            data = load_json(source)
            pure_name = file_name[:-5]
            code = json2code(data, pure_name, types[file_name])
            content.append(code)

    stats = make_stats()
    stats_code = json2code(stats, "stats" , types["stats.json"])

    content.append(stats_code)
    with open(os.path.join(dist, "assets.ts"), 'wt', encoding="utf-8") as f:
        f.write("\n".join(content))

emptyDir(dist)
make()