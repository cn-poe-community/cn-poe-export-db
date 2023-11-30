import json
import sys
import urllib.request
import re

en_tree_url = "https://www.pathofexile.com/passive-skill-tree"
zh_tree_url = "https://poe.game.qq.com/passive-skill-tree"


en_tree_file = "../../docs/tree/en_tree.json"
zh_tree_file = "../../docs/tree/zh_tree.json"

notables_json_file = "../../assets/passiveskills/notables.json"
keystones_json_file = "../../assets/passiveskills/keystones.json"
ascendant_json_file = "../../assets/passiveskills/ascendant.json"

def load_json(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data


def download_trees():
    en_tree = download_tree(en_tree_url, en_tree_file)
    zh_tree = download_tree(zh_tree_url, zh_tree_file)
    return en_tree, zh_tree

def load_trees():
    return load_json(en_tree_file),load_json(zh_tree_file)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"


def download_tree(url: str, save_path: str):
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={'User-agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        tree_text = get_tree_from_html(html)
        with open(f'{save_path}', 'wt', encoding="utf-8") as f:
            f.write(tree_text)
        print(f"downloaded {url} to {save_path}")
        return json.loads(tree_text)


def get_tree_from_html(html: str) -> str:
    html = html.replace("\n", "")
    pattern = re.compile(
        r"var passiveSkillTreeData = (\{.+?\});")
    m = pattern.search(html)
    return m.group(1)


def init_notable_nodes(en_nodes, zh_nodes):
    '''初始化大点天赋json文件
    '''
    node_list = []
    nodes = {}
    for id, node in en_nodes.items():
        if 'name' not in node:
            continue
        name = node['name']
        if 'recipe' in node:
            data = {"id": id, "en": name}
            node_list.append(data)
            nodes[id] = data

    name_counts = {}
    for id, node in zh_nodes.items():
        if id not in nodes:
            continue
        name = node['name']
        if name not in name_counts:
            name_counts[name] = 1
        else:
            name_counts[name] += 1

        nodes[id]["zh"] = name

    node_list = [node for node in node_list if name_counts[node["zh"]] == 1]

    with open(notables_json_file, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))
    print(f"initiated {notables_json_file}")


def init_keystone_nodes(en_nodes, zh_nodes):
    '''初始化基石天赋json文件
    '''
    node_list = []
    nodes = {}
    for id, node in en_nodes.items():
        if 'name' not in node:
            continue
        name = node['name']
        if 'isKeystone' in node and node['isKeystone']:
            data = {"id": id, "en": name}
            node_list.append(data)
            nodes[id] = data

    for id, node in zh_nodes.items():
        if id not in nodes:
            continue
        name = node['name']
        nodes[id]['zh'] = name

    check_repeated_zh_keystones(node_list)

    with open(keystones_json_file, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))
    print(f"initiated {keystones_json_file}")


def check_repeated_zh_keystones(node_list):
    zh_set = set()
    for node in node_list:
        zh = node["zh"]
        if zh in zh_set:
            raise Exception(f"repeated zh keystones: {zh}")


hidden_ascendants = [{"id": "18054", "zh": "自然之怒", "en": "Fury of Nature"},
                     {"id": "57331", "zh": "虚空掌控", "en": "Harness the Void"},
                     {"id": "27602", "zh": "九条命", "en": "Nine Lives"},
                     {"id": "57568", "zh": "炽热净化", "en": "Searing Purity"},
                     {"id": "52435", "zh": "不屈坚毅", "en": "Indomitable Resolve"},
                     {"id": "42469", "zh": "致命绽放", "en": "Fatal Flourish"},
                     {"id": "19355", "zh": "释放潜能", "en": "Unleashed Potential"}]


def init_ascendant_nodes(en_nodes, zh_nodes):
    '''初始化升华json文件
    '''
    node_list = []
    nodes = {}
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
        nodes[id] = data

    for id, node in zh_nodes.items():
        if id not in nodes:
            continue
        zh_name = node['name']
        nodes[id]["zh"] = zh_name

    # 目前贵族与刺客存在相同的升华天赋名称：暗影
    # 将贵族版本改为 暗影（贵族）
    # 详情见本项目README.md
    for id, node in enumerate(node_list):
        if node["en"] == "Assassin" and node["zh"] != "暗影" \
                or node["en"] == "Opportunistic" and node["zh"] != "暗影":
            raise Exception("升华名称 暗影 不再重复")

    for id, node in enumerate(node_list):
        if node["en"] == "Assassin" and node["zh"] == "暗影":
            node["zh"] = "暗影（贵族）"
            break

    for ascendant in hidden_ascendants:
        node_list.append(ascendant)

    check_repeated_zh_ascendants(node_list)

    with open(ascendant_json_file, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))
    print(f"initiated {ascendant_json_file}")


def check_repeated_zh_ascendants(node_list):
    zh_set = set()
    for node in node_list:
        zh = node["zh"]
        if zh in zh_set:
            raise Exception(f"warning: repeated zh ascendants: {zh}")


if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1] == "-un":
        en_tree,zh_tree = load_trees()
    else:
        en_tree, zh_tree = download_trees()
    
    en_nodes, zh_nodes = en_tree["nodes"], zh_tree["nodes"]
    init_notable_nodes(en_nodes, zh_nodes)
    init_keystone_nodes(en_nodes, zh_nodes)
    init_ascendant_nodes(en_nodes, zh_nodes)
