import json

tree_file = "../docs/tree/3.21/tree.json"
zh_tree_file = "../docs/tree/3.21/zh_tree.json"


def get_nodes(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
        nodes = data['nodes']
        return nodes


def init_notable_nodes():
    nodes = get_nodes(tree_file)
    zh_nodes = get_nodes(zh_tree_file)

    node_list = []
    node_map = {}
    for id, node in nodes.items():
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

    with open('../src/passiveskills/notables.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False,indent=4))


def init_keystone_nodes():
    nodes = get_nodes(tree_file)
    zh_nodes = get_nodes(zh_tree_file)

    node_list = []
    node_map = {}
    for id, node in nodes.items():
        if 'name' not in node:
            continue
        name = node['name']
        if 'isKeystone' in node and node['isKeystone']:
            data = {"id": id, "en": name}
            node_list.append(data)
            node_map[id] = data

    names = set()
    for id, node in zh_nodes.items():
        if id not in node_map:
            continue
        name = node['name']
        if name not in names:
            names.add(name)
        else:
            print(f"warning: repeated keystone name: {name}")

        node_map[id]['zh'] = name

    with open('../src/passiveskills/keystones.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(node_list, ensure_ascii=False, indent=4))


def init_ascendant_nodes():
    nodes = get_nodes(tree_file)
    zh_nodes = get_nodes(zh_tree_file)

    nodes_list = []
    nodes_map = {}
    for id, node in nodes.items():
        if 'name' not in node:
            continue
        if 'ascendancyName' not in node:
            continue
        if not ("isNotable" in node or "isMultipleChoiceOption" in node):
            continue

        name = node['name']
        data = {"id": id, "en": "name"}
        nodes_list.append(data)
        nodes_map[id] = data

    for id, node in zh_nodes.items():
        if id not in nodes_map:
            continue

        zh_name = node['name']
        nodes_map[id]["zh"] = zh_name
    
    # 目前贵族与刺客存在相同的升华天赋名称：暗影
    # 将贵族版本改为 暗影(贵族)
    # 详情见本项目README.md
    for id, node in enumerate(nodes_list):
        if node["en"] == "Assassin" and node["zh"] == "暗影":
            node["zh"] = "暗影(贵族)"
            break
    nodes_list.append({"id": "18054", "zh": "自然之怒", "en": "Fury of Nature"})
    nodes_list.append({"id": "57331", "zh": "虚空掌控", "en": "Harness the Void"})
    nodes_list.append({"id": "27602", "zh": "九条命", "en": "Nine Lives"})
    nodes_list.append({"id": "57568", "zh": "炽热净化", "en": "Searing Purity"})
    nodes_list.append({"id": "52435", "zh": "不屈坚毅",
                      "en": "Indomitable Resolve"})
    nodes_list.append({"id": "42469", "zh": "致命绽放", "en": "Fatal Flourish"})
    nodes_list.append({"id": "19355", "zh": "释放潜能", "en": "Unleashed Potential"})

    with open('../src/passiveskills/ascendant.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(nodes_list, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    init_notable_nodes()
    init_keystone_nodes()
    init_ascendant_nodes()
