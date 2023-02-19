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
    files = ["../src/stats/main.json", "../src/stats/append.json"]

    for file in files:
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            statlist = []

            for stat in data:
                stat["zh"] = format(stat["zh"])
                stat["en"] = format(stat["en"])

            with open(f'{file}.new.json', 'wt', encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
