# gems.js
import json


def dict_2_javascript(data, name):
    js = []
    js.append(f'export const {name} = new Map([')
    kBuf = []
    for k, _ in data.items():
        kBuf.append(k)
    for i in range(len(kBuf)):
        k = kBuf[i]
        v = data[k]
        if i == len(kBuf)-1:
            js.append(
                f'[{json.dumps(k,ensure_ascii=False)},{json.dumps(v,ensure_ascii=False)}]')
        else:
            js.append(
                f'[{json.dumps(k,ensure_ascii=False)},{json.dumps(v,ensure_ascii=False)}],')
    js.append("]);\n")

    return "".join(js)


def save_dict_as_javascript(path, data, name):
    with open(path, 'wt', encoding="utf-8") as f:
        f.write(dict_2_javascript(data, name))


def save_dicts_as_javascript(path, pairs):
    with open(path, 'wt', encoding="utf-8") as f:
        for pair in pairs:
            data = pair[0]
            name = pair[1]
            f.write(dict_2_javascript(data, name))


def init_gems():
    with open('./gems.json', 'rt', encoding="utf-8") as f:
        data = json.loads(f.read())

        skills = {}
        for gem_id, gem_v in data.items():
            for _, skill_v in gem_v["skills"].items():
                baseType = skill_v["baseType"]
                zhBaseType = skill_v["zhBaseType"]
                if zhBaseType in skills:
                    print(f"发现重复的中文技能名称，请检查后重新生成：{zhBaseType}")
                skills[zhBaseType] = baseType

    save_dict_as_javascript('./js/skills.js', skills, 'skills')


def init_uniques():
    files = ["./accessories.json", "./armour.json",
             "./flasks.json", "./jewels.json", "./weapons.json"]

    uniques = {}
    for file in files:
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            for baseType, baseType_v in data.items():
                for u_id, u_v in baseType_v["uniques"].items():
                    zhName = u_v["zhName"]
                    unique = {"baseType": baseType,
                              "zhBaseType": baseType_v["zhBaseType"],
                              "name": u_id,
                              "zhName": u_v["zhName"]}
                    if zhName in uniques:
                        if type(uniques[zhName]) is list:
                            uniques[zhName].append(unique)
                        else:
                            uniques[zhName] = [uniques[zhName], unique]
                    else:
                        uniques[zhName] = unique

    save_dict_as_javascript('./js/uniques.js', uniques, 'uniques')


def init_basetypes():
    files = ["./accessories.json", "./armour.json",
             "./flasks.json", "./jewels.json", "./weapons.json"]

    for file in files:
        indexs = {}
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            for basetype, basetype_v in data.items():
                zh_basetype = basetype_v["zhBaseType"]
                if zh_basetype in indexs:
                    if type(indexs[zh_basetype]) is list:
                        indexs[zh_basetype].append(basetype)
                    else:
                        indexs[zh_basetype] = [indexs[zh_basetype], basetype]
                else:
                    indexs[zh_basetype] = basetype

        base_name = file[2:-5]
        save_dict_as_javascript(f'./js/{base_name}.js', indexs, f'{base_name}')

def init_properties():
    with open('./properties.json', 'rt', encoding="utf-8") as f:
        data = json.loads(f.read())
        keys = data["keys"]
        values = data["values"]

        propertyKeys = {}
        for key_id, key_v in keys.items():
            en = key_v["key"]
            zh = key_v["zhKey"]
            propertyKeys[zh] = en

        propertyValues = {}
        for value_id, value_v in keys.items():
            en = value_v["key"]
            zh = value_v["zhKey"]
            propertyValues[zh] = en

        pairs = [[propertyKeys, "propertyKeys"],
                 [propertyValues, "propertyValues"]]

        save_dicts_as_javascript("./js/properties.js", pairs)

def init_requirements():
    with open('./requirements.json', 'rt', encoding="utf-8") as f:
        data = json.loads(f.read())
        keys = data["keys"]
        values = data["values"]

        requirementKeys = {}
        for key_id, key_v in keys.items():
            en = key_v["key"]
            zh = key_v["zhKey"]
            requirementKeys[zh] = en

        requirementValues = {}
        for value_id, value_v in keys.items():
            en = value_v["key"]
            zh = value_v["zhKey"]
            requirementValues[zh] = en

        pairs = [[requirementKeys, "requirementKeys"],
                 [requirementValues, "requirementValues"]]

        save_dicts_as_javascript("./js/requirements.js", pairs)


if __name__ == "__main__":
    init_gems()
    init_uniques()
    init_basetypes()
    init_properties()
    init_requirements()
