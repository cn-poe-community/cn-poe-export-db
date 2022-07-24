import json

tree_file = "../docs/tree/tree_3.18.json"
zh_tree_file = "../docs/tree/zh_tree_3.18.json"


def get_nodes(file):
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
        nodes = data['nodes']
        return nodes


def init_notable_nodes():
    nodes = get_nodes(tree_file)
    zh_nodes = get_nodes(zh_tree_file)

    nodes_dict = {}
    for key, value in nodes.items():
        id = key
        if 'name' not in value:
            continue
        name = value['name']
        if 'recipe' in value:
            nodes_dict[id] = {'name': {'0': name}}

    name_counts = {}
    for key, value in zh_nodes.items():
        id = key
        if id not in nodes_dict:
            continue
        if 'name' not in value:
            continue
        name = value['name']
        if name not in name_counts:
            name_counts[name] = 1
        else:
            name_counts[name] += 1

        nodes_dict[id]['name']['1'] = name

    for key, value in zh_nodes.items():
        id = key
        if id not in nodes_dict:
            continue
        if 'name' not in value:
            continue
        name = value['name']
        if name_counts[name] == 1:
            continue
        nodes_dict[id]['stats'] = {"1": "\\n".join(value["stats"])}

    with open('../passiveskills/notables.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(nodes_dict, ensure_ascii=False))

def init_keystone_nodes():
    nodes = get_nodes(tree_file)
    zh_nodes = get_nodes(zh_tree_file)

    nodes_dict = {}
    for key, value in nodes.items():
        id = key
        if 'name' not in value:
            continue
        name = value['name']
        if 'isKeystone' in value and value['isKeystone']:
            nodes_dict[id] = {'name': {'0': name}}

    names = set()
    for key, value in zh_nodes.items():
        id = key
        if id not in nodes_dict:
            continue
        name = value['name']
        if name not in names:
            names.add(name)
        else:
            print(f"warning: repeated keystone name: {name}")

        nodes_dict[id]['name']['1'] = name

    with open('../passiveskills/keystones.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(nodes_dict, ensure_ascii=False))

def init_ascendant_nodes():
    nodes = get_nodes(tree_file)
    zh_nodes = get_nodes(zh_tree_file)

    nodes_dict = {}
    for key, value in nodes.items():
        id = key
        if 'name' not in value:
            continue
        if 'ascendancyName' not in value:
            continue
        if not ("isNotable" in value or "isMultipleChoiceOption" in value):
            continue

        name = value['name']
        nodes_dict[id] = {'name': {'0': name}}

    for key, value in zh_nodes.items():
        id = key
        if id not in nodes_dict:
            continue

        name = value['name']
        nodes_dict[id]['name']['1'] = name

    with open('../passiveskills/ascendant.json', 'wt', encoding="utf-8") as f:
        f.write(json.dumps(nodes_dict, ensure_ascii=False))

if __name__ == "__main__":
    #init_notable_nodes()
    #init_keystone_nodes()
    init_ascendant_nodes()
