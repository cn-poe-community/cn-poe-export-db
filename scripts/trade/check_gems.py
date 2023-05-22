import json


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


def load_skills():
    skills = set()
    db = load_json("../../assets/gems.json")
    for gem in db:
        list = gem["skills"]
        for skill in list:
            skills.add(skill["zh"])
    return skills

def check():
    skills = load_skills()
    data = load_json("../../docs/trade/zh_items.json")
    entries = getEntries(data,"gems")
    for entry in entries:
        type:str = entry["type"]
        type = type.replace("(","（").replace(")", "）")
        if type not in skills:
            print(f"{type} missed")

if __name__ == "__main__":
    check()