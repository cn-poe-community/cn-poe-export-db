import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.parse

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"


def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


config: dict = load_json("../config.json")

project_root = config.get("projectRoot")


def downlaod_page(url) -> str:
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={
                                 'User-agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        return html


def parse_uniques_page(html) -> list:
    pattern = r'<a class="item_unique" data-hover="([^\"]+)?" href="[^\"]+">([^/<>]+?)</a>'
    array = re.findall(pattern, html)
    uniques = []
    if len(array) == 0:
        pattern = pattern.replace('"', "'")
        array = re.findall(pattern, html)

    for unique in array:
        preview_url: str = urllib.parse.unquote_plus(unique[0])
        fullname: str = unique[1]
        slice = fullname.rsplit(" ", maxsplit=1)
        if len(slice) != 2:
            print("warning: skiped ", fullname)
            continue
        zh_name = slice[0]
        basetype = slice[1]

        en_name = preview_url.rsplit("&n=", 1)[-1]

        uniques.append({"preview_url": preview_url,
                       "fullname": fullname, "en": en_name, "zh": zh_name, "basetype": basetype})

    return uniques


items_folder = "assets/items"

data_list = {}
basetypes = {}  # 使用中文名称索引所有basetype


def add_uniques(new_uniques):
    new_uniques = [u for u in new_uniques if not is_ascii(u["zh"])]

    for file_name in os.listdir(os.path.join(project_root, items_folder)):
        full_path = os.path.join(project_root, items_folder, file_name)
        if os.path.isfile(full_path) and file_name.endswith(".json"):
            data = load_json(full_path)
            data_list[full_path] = data

            for basetype in data:
                zh = basetype["zh"]
                if zh in basetypes:
                    basetypes[zh] = basetypes[zh].append(basetype)
                else:
                    basetypes[zh] = [basetype]

    for new_unique in new_uniques:
        fullname = new_unique["fullname"]
        zh_basetype_name = new_unique["basetype"]
        if zh_basetype_name not in basetypes:
            print(
                f"warning: 跳过 {fullname} 因为未知的 basetype")
            continue
        for basetype in basetypes[zh_basetype_name]:
            if "uniques" not in basetype:
                basetype["uniques"] = [
                    {"zh": new_unique["zh"], "en": new_unique["en"]}]
            else:
                uniques: list = basetype["uniques"]
                exist = False
                for unique in uniques:
                    if unique["zh"] == new_unique["zh"]:
                        exist = True
                        print(f"{fullname} 已存在")
                        break
                if exist:
                    continue
                uniques.append(
                    {"zh": new_unique["zh"], "en": new_unique["en"]})

        if len(basetypes[zh_basetype_name]) > 1:
            print(
                f"warning: 插入了重复的暗金，因为存在重复的 basetype，请手动检查并删除多余的数据")

    for full_path in data_list.keys():
        data = data_list[full_path]

        with open(full_path, 'wt', encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


league_uniques_page = "https://poedb.tw/cn/Necropolis_league#%E6%AD%BB%E5%AF%82%E4%BA%A1%E5%9F%8E%E4%BC%A0%E5%A5%87"

if __name__ == "__main__":
    html = downlaod_page(league_uniques_page)
    new_uniques = parse_uniques_page(html)
    add_uniques(new_uniques)
