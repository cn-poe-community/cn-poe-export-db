import json


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data

def format(old_file):
    old_data:dict = load_json(old_file)

    new_data = []
    for id,obj in old_data.items():
        print(id,obj)
        texts = obj["text"]
        en = texts['0']
        zh = texts['1']

        new_data.append({"zh":zh,"en":en})

    with open(f'{old_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(new_data, ensure_ascii=False, indent=4))

def append():
    properties_file = "../src/properties.json"
    item_classes_file = "./item_classes.json"

    properties_data = load_json(properties_file)
    item_classes_data = load_json(item_classes_file)

    for property in properties_data:
        values = []
        if property["zh"] == "物品类别":
            for key,value in item_classes_data.items():
                values.append({"zh":key,"en":value})
            property["values"] = values
            break
    
    with open(f'{properties_file}.new.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(properties_data, ensure_ascii=False, indent=4))
    



if __name__ == "__main__":
    #old_file = "../src/property_keys.json"
    #format(old_file)
    append()