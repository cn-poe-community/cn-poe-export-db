import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


if __name__ == "__main__":
    files = ["../stats.json"]

    for file in files:
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            for stat, stat_content in data.items():
                if "text" in stat_content:
                    texts = stat_content["text"]
                    new_texts = {}
                    if("1") in texts:
                        new_texts["0"] = texts["1"]
                    if("9") in texts:
                        new_texts["1"] = texts["9"]
                    data[stat]["text"] = new_texts


            with open(f'{file}.new.json', 'wt', encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False))
