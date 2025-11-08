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


def download_page(url) -> str:
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={
                                 'User-agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        page = response.read().decode('utf-8')
        return page


poedb_site = "https://poedb.tw"
poedb_caches_file = "./poedb_caches.json"
poedb_caches = {}
poedb_caches_changed = False


def load_poedb_caches():
    global poedb_caches
    if Path(poedb_caches_file).is_file():
        poedb_caches = load_json(poedb_caches_file)


def save_poedb_caches():
    with open(poedb_caches_file, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(poedb_caches, ensure_ascii=False))


def get_poedb_cache(url):
    if url in poedb_caches:
        return poedb_caches[url]
    return None


def set_poedb_cache(url, page):
    global poedb_caches_changed

    poedb_caches[url] = page
    poedb_caches_changed = True


def poedb_request(url: str):
    if url.startswith(poedb_site):
        url = url[len(poedb_site):]

    cache = get_poedb_cache(url)
    if cache is not None:
        return cache

    page = download_page(poedb_site+url)
    set_poedb_cache(url, page)

    return page


def item_type_of_preview_url(url):
    if "Metadata/Items/Armours/Boots" in url:
        return "boots.json"
    if "Metadata/Items/Armours/BodyArmours" in url:
        return "body_armours.json"
    if "Metadata/Items/Armours/Helmets" in url:
        return "helmets.json"
    if "Metadata/Items/Armours/Gloves" in url:
        return "gloves.json"
    if "Metadata/Items/Tinctures" in url:
        return "flasks.json"
    if "Metadata/Items/Rings" in url:
        return "rings.json"
    if "Metadata/Items/Weapons/OneHandWeapons" in url:
        return "weapons.json"
    return None


def parse_preview(page):
    pattern = re.compile(
        r'<div class="content">.+?<div>(.+?)</div>\s+</div>', re.DOTALL)
    matches = re.search(pattern, page)
    if matches is not None:
        en = matches.group(1).strip()

    return {"en": en}


def find_base_types(page) -> list:
    pattern = r'<a class="whiteitem" data-hover="([^\"]+)?" href="[^\"]+">([^/<>]+?)</a>'
    array = re.findall(pattern, page)
    base_types = []
    if len(array) == 0:
        pattern = pattern.replace('"', "'")
        array = re.findall(pattern, page)

    for matches in array:
        hover_link = urllib.parse.unquote_plus(matches[0])
        type = item_type_of_preview_url(hover_link)
        if type is None:
            print(f"warning: type missed of {matches[1]} {hover_link}")
            continue

        preview_url = urllib.parse.urljoin(
            "https://poedb.tw/cn/hover", hover_link)
        preview = poedb_request(preview_url)
        data = parse_preview(preview)

        data["type"] = type
        data["zh"] = matches[1].strip()

        base_types.append(data)
    
    return base_types


def add_base_types(base_types):
    new_bt_type_idx = {}
    for bt in base_types:
        type = bt["type"]
        if type in new_bt_type_idx:
            new_bt_type_idx[type].append(bt)
        else:
            new_bt_type_idx[type] = [bt]

    for file_name in os.listdir(os.path.join(project_root, items_folder)):
        if file_name not in new_bt_type_idx:
            continue

        full_path = os.path.join(project_root, items_folder, file_name)
        if os.path.isfile(full_path) and file_name.endswith(".json"):
            data = load_json(full_path)
            zh_set = set()
            en_set = set()
            new_zh_set = set()

            for bt in data:
                zh = bt["zh"]
                en = bt["en"]
                zh_set.add(zh)
                en_set.add(en)

            for new_bt in new_bt_type_idx[file_name]:
                zh = new_bt["zh"]
                en = new_bt["en"]
                new_zh_set.add(zh)
                if zh in zh_set and en in en_set:
                    continue
                if zh in zh_set or en in en_set:
                    print(f"warning: zh or en changed: {zh} {en}")
                data.append({"zh": zh, "en": en})
            
            print(new_zh_set.difference(zh_set))
            print(zh_set.difference(new_zh_set))

        with open(full_path, 'wt', encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))
    pass


def find_uniques(page) -> list:
    pattern = r'<a class="uniqueitem" data-hover="([^"]+?)" href="[^"]+?"><span class="uniqueName">(.+?)</span> <span class="uniqueTypeLine">(.+?)</span></a>'
    array = re.findall(pattern, page)
    uniques = []
    if len(array) == 0:
        pattern = pattern.replace('"', "'")
        array = re.findall(pattern, page)

    for unique in array:
        preview_url: str = urllib.parse.unquote_plus(unique[0])
        zh_name = unique[1]
        basetype = unique[2]
        print(zh_name)

        en_name = preview_url.rsplit("&n=", 1)[-1]

        uniques.append({"preview_url": preview_url,
                       "fullname": "{zh_name} {basetype}", "en": en_name, "zh": zh_name, "basetype": basetype})

    return uniques


items_folder = "assets/items"

data_list = {}
base_type_zh_idx = {}  # 使用中文名称索引所有basetype


def add_uniques(new_uniques):
    new_uniques = [u for u in new_uniques if not is_ascii(u["zh"])]

    for file_name in os.listdir(os.path.join(project_root, items_folder)):
        full_path = os.path.join(project_root, items_folder, file_name)
        if os.path.isfile(full_path) and file_name.endswith(".json"):
            data = load_json(full_path)
            data_list[full_path] = data

            for basetype in data:
                zh = basetype["zh"]
                if zh in base_type_zh_idx:
                    base_type_zh_idx[zh] = base_type_zh_idx[zh].append(
                        basetype)
                else:
                    base_type_zh_idx[zh] = [basetype]

    for new_unique in new_uniques:
        fullname = new_unique["fullname"]
        zh_basetype_name = new_unique["basetype"]
        if zh_basetype_name not in base_type_zh_idx:
            print(
                f"warning: 跳过 {fullname} 因为未知的 basetype")
            continue
        for basetype in base_type_zh_idx[zh_basetype_name]:
            if "uniques" not in basetype:
                basetype["uniques"] = [
                    {"zh": new_unique["zh"], "en": new_unique["en"]}]
            else:
                uniques: list = basetype["uniques"]
                exist = False
                for unique in uniques:
                    if unique["zh"] == new_unique["zh"]:
                        exist = True
                        break
                if exist:
                    continue
                uniques.append(
                    {"zh": new_unique["zh"], "en": new_unique["en"]})

        if len(base_type_zh_idx[zh_basetype_name]) > 1:
            print(
                f"warning: 插入了重复的暗金，因为存在重复的 basetype，请手动检查并删除多余的数据")

    for full_path in data_list.keys():
        data = data_list[full_path]

        with open(full_path, 'wt', encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


league_url = "https://poedb.tw/cn/Mercenaries_league"

if __name__ == "__main__":
    load_poedb_caches()

    page = poedb_request(league_url)

    base_types = find_base_types(page)
    add_base_types(base_types)

    new_uniques = find_uniques(page)
    add_uniques(new_uniques)

    if poedb_caches_changed:
        save_poedb_caches()
