import json


def load_json(file: str):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


data = load_json("./armour.json")

body_armours = []
boots = []
gloves = []
helmets = []
shields = []
quivers = []

for item in data:
    zh: str = item["zh"]
    if zh.endswith("衣") or zh.endswith("锁甲") or zh.endswith("环甲") or zh.endswith("铠") or zh.endswith("外套") or\
        zh.endswith("背心") or zh.endswith("链甲") or zh.endswith("皮甲"):
        body_armours.append(item)
    elif zh.endswith("之履") or zh.endswith("胫甲") or zh.endswith("鞋") or zh.endswith("靴") or\
            zh.endswith("鞋") or zh.startswith("异色鞋") or zh.endswith("腿"):
        boots.append(item)
    elif zh.endswith("手甲") or zh.endswith("手套") or zh.endswith("手") or zh.endswith("臂甲"):
        gloves.append(item)
    elif zh.endswith("面具") or zh.endswith("盔") or zh.endswith("冠") or zh.endswith("环") or\
            zh.endswith("笼") or zh.endswith("兜") or zh.endswith("之面") or zh.endswith("帽"):
        helmets.append(item)
    elif zh.endswith("盾"):
        shields.append(item)
    elif zh.endswith("箭袋"):
        quivers.append(item)
    else:
        body_armours.append(item)

with open("./body_armours.json", 'wt', encoding="utf-8") as f:
    f.write(json.dumps(body_armours, ensure_ascii=False, indent=4))

with open("./boots.json", 'wt', encoding="utf-8") as f:
    f.write(json.dumps(boots, ensure_ascii=False, indent=4))

with open("./gloves.json", 'wt', encoding="utf-8") as f:
    f.write(json.dumps(gloves, ensure_ascii=False, indent=4))

with open("./helmets.json", 'wt', encoding="utf-8") as f:
    f.write(json.dumps(helmets, ensure_ascii=False, indent=4))

with open("./shields.json", 'wt', encoding="utf-8") as f:
    f.write(json.dumps(shields, ensure_ascii=False, indent=4))

with open("./quivers.json", 'wt', encoding="utf-8") as f:
    f.write(json.dumps(quivers, ensure_ascii=False, indent=4))