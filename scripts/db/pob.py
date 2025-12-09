import json
import os
import subprocess
from common import at, must_parent
from config import POB_PATH


def get_latest_tree_version() -> str:
    wd = at("scripts/luajit")
    env = os.environ.copy()
    env["LUA_PATH"] = f"{POB_PATH}/?.lua;{POB_PATH}/lua/?.lua;"

    result = subprocess.run(["luajit/luajit.exe", "-e", "local m = require 'GameVersions'; print(latestTreeVersion)"],
                            capture_output=True,
                            text=True,
                            cwd=wd,
                            env=env)
    if result.stderr.strip() != "":
        raise Exception(f"POB: 获取最新天赋树版本失败 {result.stderr.strip()}")
    return result.stdout.strip()


def get_pob_tree(version: str):
    wd = at("scripts/luajit")
    env = os.environ.copy()
    env["LUA_PATH"] = f"{POB_PATH}/lua/?.lua;{POB_PATH}/TreeData/{version}/?.lua;"

    result = subprocess.run(["luajit/luajit.exe", "-e", "local j = require 'dkjson';local t = require 'tree'; print(j.encode(t))"],
                            capture_output=True,
                            text=True,
                            cwd=wd,
                            env=env)
    if result.stderr.strip() != "":
        raise Exception(f"POB: 获取最新天赋树失败: {result.stderr.strip()}")
    return json.loads(result.stdout.strip())

# TODO: 生成的内容需要根据实际需求更新


def generate_slim_tree_for_creator():
    '''pob-building-creator所需的POB天赋树'''
    tree_version = get_latest_tree_version()
    pob_tree = get_pob_tree(tree_version)

    slim_tree = {k: pob_tree[k] for k in pob_tree if k in ["classes"]}

    for c in slim_tree["classes"]:
        if "background" in c:
            del c["background"]
        if "ascendancies" in c:
            for a in c["ascendancies"]:
                if "background" in a:
                    del a["background"]

    saved = at("db/pob/tree.json")
    must_parent(saved)
    with open(saved, 'wt', encoding='utf-8') as f:
        json.dump(slim_tree, f, ensure_ascii=False, indent=2)
