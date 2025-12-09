import sys
from make import js
from db import gem, item, pair, passiveskill, pob, stat, unique
from export import game, trade, tree

def prepare(files:str|None):
    if files == "game" or files is None:
        game.export_game_files("tencent")
        game.export_game_files("global")
    if files == "trade" or files is None:
        trade.download_trade_files()
    if files == "tree" or files is None:
        tree.download_passive_skill_trees()


def run_tasks():
    #pob.generate_slim_tree_for_creator()
    pair.update_attributes()
    pair.update_properties()
    pair.update_requirements()
    unique.update()
    item.create_items()
    gem.create_gems()
    passiveskill.create_nodes()
    stat.create_stats()

def make():
    js.make()

def main():
    """主函数，处理命令行参数
    1. prepare [game|trade|tree] 准备数据文件
    2. (无参数) 执行所有数据更新任务
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "prepare":
            prepare(sys.argv[2] if len(sys.argv) > 2 else None)
        elif sys.argv[1] == "make":
            make()
    else:
        run_tasks()


if __name__ == "__main__":
    main()
