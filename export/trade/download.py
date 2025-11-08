import json
import os
from pathlib import Path
import re
import urllib.request

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

parent_dir = os.path.dirname(os.path.abspath(__file__))


def relative(*paths: str) -> str:
    '''获取相对于当前文件的路径，支持多个路径参数'''
    return os.path.join(parent_dir, *paths)


def must_parent(path: str) -> None:
    '''确保文件所在路径存在'''
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_json(file: str) -> dict:
    '''加载json文件'''
    with open(file, 'rt', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    return data

# --- trade files

global_trade_urls = ["https://www.pathofexile.com/api/trade/data/stats",
                     "https://www.pathofexile.com/api/trade/data/static",
                     "https://www.pathofexile.com/api/trade/data/items",
                     "https://www.pathofexile.com/api/trade/data/filters"]

tencent_trade_urls = ["https://poe.game.qq.com/api/trade/data/stats",
                      "https://poe.game.qq.com/api/trade/data/static",
                      "https://poe.game.qq.com/api/trade/data/items",
                      "https://poe.game.qq.com/api/trade/data/filters"]


def download_trade_file(url: str, saved_path: str):
    headers = {'User-agent': USER_AGENT}

    print(f"downloading {url} to {saved_path}")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        must_parent(saved_path)
        with open(saved_path, 'wt', encoding="utf-8") as f:
            f.write(content)
    print(f"download success")


def download_trade_files():
    for url in global_trade_urls:
        base_name = url.split("/")[-1]
        saved_path = relative("global/", f"{base_name}.json")
        download_trade_file(url, saved_path)
        pass
    for url in tencent_trade_urls:
        base_name = url.split("/")[-1]
        saved_path = relative("tencent/", f"{base_name}.json")
        download_trade_file(url, saved_path)


global_tree_url = "https://www.pathofexile.com/passive-skill-tree"
tencent_tree_url = "https://poe.game.qq.com/passive-skill-tree"

def get_tree_from_html(html: str) -> str:
    html = html.replace("\n", "")
    pattern = re.compile(
        r"var passiveSkillTreeData = (\{.+?\});")
    m = pattern.search(html)
    return m.group(1)


def download_tree(url: str, save_path: str):
    must_parent(save_path)
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={'User-agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        tree_text = get_tree_from_html(html)
        with open(f'{save_path}', 'wt', encoding="utf-8") as f:
            f.write(tree_text)
        print(f"saved {save_path}")

def download_trees():
    download_tree(global_tree_url, relative("global/passive_skill_tree.json"))
    download_tree(tencent_tree_url, relative("tencent/passive_skill_tree.json"))

if __name__ == "__main__":
    download_trade_files()
    download_trees()
