import json
import os


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def getEntries(data, labelId):
    result = data["result"]
    for part in result:
        id = part["id"]
        if id == labelId:
            return part["entries"]


basetypes = set()
uniques = {}


def load_db_items():
    folder = "../../assets/items"
    for file_name in os.listdir(folder):
        full_path = os.path.join(folder, file_name)
        if os.path.isfile(full_path) and file_name.endswith(".json"):
            json = load_json(full_path)
            for item in json:
                basetype = item["zh"]
                basetypes.add(basetype)
                if "uniques" in item:
                    for u in item["uniques"]:
                        zh_full_name = u["zh"] + " " + basetype
                        uniques[zh_full_name] = u


def check_items():
    load_db_items()
    data = load_json("../../docs/trade/tx/items")
    labelIds = ["accessory", "armour", "flask", "jewel", "weapon"]
    for id in labelIds:
        entries = getEntries(data, id)
        for entry in entries:
            type = entry["type"]
            if type not in basetypes:
                print(f"{type} missed")
            if 'flags' in entry and 'unique' in entry["flags"]:
                text = entry["text"]
                if text not in uniques:
                    print(f"unique {text} missed")


if __name__ == "__main__":
    check_items()
