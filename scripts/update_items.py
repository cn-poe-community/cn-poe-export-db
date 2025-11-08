import json
import os
from pathlib import Path
import ndjson

def must_parent(path: str) -> None:
    '''确保文件所在路径存在, 常用于写入文件时，避免父目录不存在而抛出异常'''
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_json(file: str):
    '''读取json文件'''
    with open(file, 'rt', encoding='utf-8') as f:
        return json.load(f)


def save_json(file: str, data) -> None:
    '''保存json文件'''
    must_parent(file)
    with open(file, 'wt', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_ndjson(file: str):
    '''读取ndjson文件'''
    with open(file, 'rt', encoding='utf-8') as f:
        return ndjson.load(f)

ITEMS = {}
BASE_TYPES = {}


def update():
    #  遍历./items
    for file in os.listdir("../assets/items"):
        if file.endswith(".json"):
            file_path = os.path.join("../assets/items", file)
            data = read_json(file_path)
            ITEMS[file] = data
    for file in os.listdir("../assets/base_types"):
        if file.endswith(".json"):
            file_path = os.path.join("../assets/base_types", file)
            data = read_json(file_path)
            BASE_TYPES[file] = data

    for each in ITEMS:
        full_name_idx = [f'{item["zh"]},{item["en"]}' for item in ITEMS[each]]
        target = BASE_TYPES[each]

        news = []
        for item in target:
            full_name = f'{item["zh"]},{item["en"]}'
            if full_name in full_name_idx:
                continue
            else:
                print(item["zh"], item["en"])
                news.append({"zh": item["zh"], "en": item["en"]})
        ITEMS[each].extend(news)
    
    uniques = read_ndjson("../assets/uniques.ndjson")

    for each in ITEMS:
        en_idx = {}
        for item in ITEMS[each]:
            en = item["en"]
            if en not in item:
                en_idx[en] = [item]
            else:
                en_idx[en].append(item)
        
        for u in uniques:
            if "baseType" not in u or not u["baseType"]:
                print(u)
                #print("unique without baseType:", u["zh"], u["en"])
                continue
            if u["baseType"] not in en_idx:
                continue
            for item in en_idx[u["baseType"]]:
                holder = []
                if "uniques" in item:
                    holder = item["uniques"]
                else:
                    item["uniques"] = holder
                find = False
                for uni in holder:
                    if uni["zh"] == u["zh"] and uni["en"] == u["en"]:
                        find = True
                        break
                if not find:
                    print("add unique:", u["zh"], u["en"], "to", item["zh"], item["en"])
                    holder.append({"zh": u["zh"], "en": u["en"]})

    
    
    for each in ITEMS:
        save_json(os.path.join("../assets/items", each), ITEMS[each])


update()
