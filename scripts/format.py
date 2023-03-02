import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def format(template: str):
    arg_index = 0
    while "(\\S+)" in template:
        template = template.replace("(\\S+)", f"{{{arg_index}}}", 1)
        arg_index += 1

    if template[0] == "^":
        template = template[1:]

    if template[-1] == "$":
        template = template[:-1]

    return template


if __name__ == "__main__":
    files = ["../src/accessories.json", "../src/armour.json",
             "../src/flasks.json", "../src/jewels.json", "../src/weapons.json"]

    for file in files:
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            list = []

            for key in data:
                basetype = {}
                value = data[key]
                en = value["text"]["0"]
                zh = value["text"]["1"]
                uniques: dict = value["uniques"]
                unique_list = []
                if len(uniques) > 0:
                    for u_key in uniques:
                        u_value = uniques[u_key]
                        u_en = u_value["text"]["0"]
                        u_zh = u_value["text"]["1"]
                        unique_list.append({"zh": u_zh, "en": u_en})
                list.append({"zh": zh, "en": en, "uniques": unique_list})

            with open(f'{file}.new.json', 'wt', encoding="utf-8") as f:
                f.write(json.dumps(list, ensure_ascii=False, indent=4))
