from pathlib import Path
import re
from typing import Any
import urllib.request

from common import SERVER_GLOBAL, SERVER_TENCENT, must_parent, read_json
from config import PROJECT_ROOT, USER_AGENT

SAVED_ROOT = PROJECT_ROOT/"export"/"tree"


def tree_file_path(server: str, filename: str):
    return SAVED_ROOT/server/filename


global_passive_skill_tree_url = "https://www.pathofexile.com/passive-skill-tree"
tencent_passive_skill_tree_url = "https://poe.game.qq.com/passive-skill-tree"


def get_passive_skill_tree_from_html(html: str) -> str:
    html = html.replace("\n", "")
    pattern = re.compile(
        r"var passiveSkillTreeData = (\{.+?\});")
    m = pattern.search(html)
    if m:
        return m.group(1)
    else:
        raise Exception("在HTML内容中未找到天赋树数据")


def download_passive_skill_tree(url: str, saved_path: str | Path):
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={'User-agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        tree_text = get_passive_skill_tree_from_html(html)
        must_parent(saved_path)
        with open(f'{saved_path}', 'wt', encoding="utf-8") as f:
            f.write(tree_text)
        print(f"saved {saved_path}")


def download_passive_skill_trees():
    download_passive_skill_tree(global_passive_skill_tree_url, tree_file_path(
        SERVER_GLOBAL, "passive_skill_tree.json"))
    download_passive_skill_tree(tencent_passive_skill_tree_url, tree_file_path(
        SERVER_TENCENT, "passive_skill_tree.json"))


def passive_skill_tree(server: str) -> Any:
    return read_json(tree_file_path(server, "passive_skill_tree.json"))
