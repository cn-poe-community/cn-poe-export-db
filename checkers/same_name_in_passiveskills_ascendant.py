import json


file = "../src/passiveskills/ascendant.json"

if __name__ == "__main__":
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)

        zh_names = set()
        for id, value in data.items():
            zh_name = value["name"]["1"]
            if zh_name in zh_names:
                print(f"warning: find repeated name: {zh_name}")
            else:
                zh_names.add(zh_name)
