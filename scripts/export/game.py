import os
import subprocess
import sys
import duckdb
from common import at


def export_game_files(client: str):
    wd = ""
    if client == "global":
        wd = at("export/game/global")
    elif client == "tencent":
        wd = at("export/game/tencent")

    env = os.environ.copy()

    process = subprocess.Popen(["npm", "exec", "pathofexile-dat"],
                               shell=True,
                               stdout=sys.stdout,
                               stderr=subprocess.STDOUT,
                               text=True,
                               cwd=wd,
                               env=env)
    return_code = process.wait()
    if return_code != 0:
        raise Exception(f"导出游戏数据失败，返回 {return_code}")


def table_path(client: str, lang: str, table: str) -> str:
    '''获取表文件路径'''
    return at("export/game", client, 'tables', lang, f"{table}.json")


loaded_tables = set()
created_idx = set()


def duck_table_name(client: str, lang: str, table: str):
    return f"{client}_{lang}_{table}".replace(" ", "_").lower()


def load_table(client: str, lang: str, table: str):
    file = table_path(client, lang, table)
    duck_name = duck_table_name(client, lang, table)

    if duck_name in loaded_tables:
        return
    loaded_tables.add(duck_name)
    duckdb.sql(f"""
    CREATE TABLE {duck_name} AS
        SELECT * FROM '{file}';
    """)


def create_index(table: str, field: str):
    idx_name = f"{table}_{field}_idx"
    if idx_name in created_idx:
        return
    created_idx.add(idx_name)
    duckdb.sql(f"CREATE INDEX {idx_name} ON {table} ({field});")
