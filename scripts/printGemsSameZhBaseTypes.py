import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


if __name__ == "__main__":
    file = "../gems.json"

    data = load_json(file)

    zhBaseTypes = set()
    for gem, v in data.items():
        for skill, skill_v in v.items():
            zhBaseType = skill_v["zhBaseType"]
            if zhBaseType in zhBaseTypes:
                print(f'{zhBaseType}')
            zhBaseTypes.add(zhBaseType)
