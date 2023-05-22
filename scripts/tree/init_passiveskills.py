import json
import urllib.request
import re

en_tree_url = "https://www.pathofexile.com/passive-skill-tree"
zh_tree_url = "https://poe.game.qq.com/passive-skill-tree"


en_tree_file = "../../docs/tree/en_tree.json"
zh_tree_file = "../../docs/tree/zh_tree.json"


def download_trees():
    en_tree = download_tree(en_tree_url, en_tree_file)
    zh_tree = download_tree(zh_tree_url, zh_tree_file)
    return en_tree, zh_tree


def download_tree(url, save_path):
    opener = AppURLopener()
    with opener.open(url) as f:
        html = f.read().decode('utf-8')
        tree_text = get_tree_text_from_html(html)
        with open(f'{save_path}', 'wt', encoding="utf-8") as f:
            f.write(tree_text)
        print(f"downloaded {url} to {save_path}")
        return json.loads(tree_text)


class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"


def get_tree_text_from_html(html: str):
    html = html.replace("\n", "")
    pattern = re.compile(
        r"var passiveSkillTreeData = (\{.+?\});")
    m = pattern.search(html)
    return m.group(1)


def init_notable_nodes(en_nodes, zh_nodes):
    node_list = []
    node_map = {}
    for id, node in en_nodes.items():
        if 'name' not in node:
            continue
        name = node['name']
        if 'recipe' in node:
            data = {"id": id, "en": name}
            node_list.append(data)
            node_map[id] = data

    name_counts = {}
    for id, node in zh_nodes.items():
        if id not in node_map:
            continue
        name = node['name']
        if name not in name_counts:
            name_counts[name] = 1
        else:
            name_counts[name] += 1

        node_map[id]["zh"] = name

    node_list = [node for node in node_list if name_counts[node["zh"]] == 1]

    with open('../../assets/passiveskills/notables.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))


def init_keystone_nodes(en_nodes, zh_nodes):
    node_list = []
    node_map = {}
    for id, node in en_nodes.items():
        if 'name' not in node:
            continue
        name = node['name']
        if 'isKeystone' in node and node['isKeystone']:
            data = {"id": id, "en": name}
            node_list.append(data)
            node_map[id] = data

    for id, node in zh_nodes.items():
        if id not in node_map:
            continue
        name = node['name']
        node_map[id]['zh'] = name
    
    check_repeated_zh_keystones(node_list)

    with open('../../assets/passiveskills/keystones.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))

def check_repeated_zh_keystones(node_list):
    zh_set = set()
    for node in node_list:
        zh = node["zh"]
        if zh in zh_set:
            print(f"warning: repeated zh keystones: {zh}")

def init_ascendant_nodes(en_nodes, zh_nodes):
    node_list = []
    node_map = {}
    for id, node in en_nodes.items():
        if 'name' not in node:
            continue
        if 'ascendancyName' not in node:
            continue
        if not ("isNotable" in node or "isMultipleChoiceOption" in node):
            continue

        name = node['name']
        data = {"id": id, "en": name}
        node_list.append(data)
        node_map[id] = data

    for id, node in zh_nodes.items():
        if id not in node_map:
            continue
        zh_name = node['name']
        node_map[id]["zh"] = zh_name

    # 目前贵族与刺客存在相同的升华天赋名称：暗影
    # 将贵族版本改为 暗影（贵族）
    # 详情见本项目README.md
    for id, node in enumerate(node_list):
        if node["en"] == "Assassin" and node["zh"] == "暗影":
            node["zh"] = "暗影（贵族）"
            break
    node_list.append({"id": "18054", "zh": "自然之怒", "en": "Fury of Nature"})
    node_list.append({"id": "57331", "zh": "虚空掌控", "en": "Harness the Void"})
    node_list.append({"id": "27602", "zh": "九条命", "en": "Nine Lives"})
    node_list.append({"id": "57568", "zh": "炽热净化", "en": "Searing Purity"})
    node_list.append({"id": "52435", "zh": "不屈坚毅",
                      "en": "Indomitable Resolve"})
    node_list.append({"id": "42469", "zh": "致命绽放", "en": "Fatal Flourish"})
    node_list.append({"id": "19355", "zh": "释放潜能",
                      "en": "Unleashed Potential"})
    
    check_repeated_zh_ascendants(node_list)

    with open('../../assets/passiveskills/ascendant.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))

def check_repeated_zh_ascendants(node_list):
    zh_set = set()
    for node in node_list:
        zh = node["zh"]
        if zh in zh_set:
            print(f"warning: repeated zh ascendants: {zh}")

if __name__ == "__main__":
    en_tree, zh_tree = download_trees()
    en_nodes, zh_nodes = en_tree["nodes"], zh_tree["nodes"]
    init_notable_nodes(en_nodes, zh_nodes)
    init_keystone_nodes(en_nodes, zh_nodes)
    init_ascendant_nodes(en_nodes, zh_nodes)
