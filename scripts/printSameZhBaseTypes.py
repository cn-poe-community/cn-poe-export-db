import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


if __name__ == "__main__":
    files = [
        "../accessories.json",
        "../armour.json",
        "../flasks.json",
        "../jewels.json",
        "../weapons.json"
    ]

    zhBaseTypes = {}

    for file in files:
        data = load_json(file)
        for k, v in data.items():
            en = k
            zh = v["zhBaseType"]
            if zh in zhBaseTypes:
                zhBaseTypes[zh].append(en)
            else:
                zhBaseTypes[zh] = [en]

    for k, v in zhBaseTypes.items():
        if len(v) > 1:
            print(f'{k},{v}')
