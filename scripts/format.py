import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


if __name__ == "__main__":
    files = ["../src/stats.json"]

    for file in files:
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            statlist = []

            for stat, stat_content in data.items():
                if "text" in stat_content:
                    texts = stat_content["text"]

                    if "0" in texts:
                        texts_0 = texts["0"]
                    if "1" in texts:
                        texts_1 = texts["1"]

                    #print(texts_1)

                    for id in texts_1:
                        if id in texts_0:
                            statlist.append({"id": stat, "zh": texts_1[id], "en": texts_0[id]})

            with open(f'{file}.new.json', 'wt', encoding="utf-8") as f:
                f.write(json.dumps(statlist, ensure_ascii=False))
