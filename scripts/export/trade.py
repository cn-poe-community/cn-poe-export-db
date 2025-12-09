import os
from pathlib import Path
import urllib.request

import duckdb

from common import SERVER_GLOBAL, SERVER_TENCENT, at, must_parent, read_json, save_json
from config import PROJECT_ROOT, USER_AGENT

SAVED_ROOT = PROJECT_ROOT/"export"/"trade"


def trade_file_path(server: str, filename: str):
    return SAVED_ROOT/server/filename


global_trade_urls = ["https://www.pathofexile.com/api/trade/data/stats",
                     "https://www.pathofexile.com/api/trade/data/static",
                     "https://www.pathofexile.com/api/trade/data/items"]

tencent_trade_urls = ["https://poe.game.qq.com/api/trade/data/stats",
                      "https://poe.game.qq.com/api/trade/data/static",
                      "https://poe.game.qq.com/api/trade/data/items"]


def download_trade_file(url: str, saved_path: str | Path):
    headers = {'User-agent': USER_AGENT}

    print(f"downloading {url} to {saved_path}")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        must_parent(saved_path)
        with open(saved_path, 'wt', encoding="utf-8") as f:
            f.write(content)
        print(f"saved {saved_path}")


def download_trade_files():
    for url in global_trade_urls:
        base_name = url.split("/")[-1]
        download_trade_file(url, trade_file_path(
            SERVER_GLOBAL, f"{base_name}.json"))
    for url in tencent_trade_urls:
        base_name = url.split("/")[-1]
        download_trade_file(url, trade_file_path(
            SERVER_TENCENT, f"{base_name}.json"))


ITEMS_EQUIPEMNT_IDS = ["accessory", "armour",
                       "flask", "jewel", "weapon", "tincture"]


def equipment_uniques(client):
    """从交易网站数据导出传奇，参数client指定客户端"""
    data = read_json(trade_file_path(client, "items.json"))
    array = []
    for category in data["result"]:
        if category["id"] not in ITEMS_EQUIPEMNT_IDS:
            continue

        entries = category["entries"]
        for entry in entries:
            if "flags" not in entry or "unique" not in entry["flags"] or not entry["flags"]["unique"]:
                continue
            u = {"name": entry["name"], "type": entry["type"]}
            array.append(u)
    return array


loaded_tables = set()


def load_table(client, table):
    """
    将数据存在数据库中，便于处理。

    支持以下表：

    - uniques，数据源自export_trade_uniques()
    """
    duck_name = f"{client}_trade_{table}".replace(" ", "_").lower()

    if duck_name in loaded_tables:
        return
    loaded_tables.add(duck_name)

    data = []
    if table == "uniques":
        data = equipment_uniques(client)
    else:
        print(f"error: [trade] 不支持的交易表 {client} {table}")
        return

    # 由于duckdb的引擎限制，这里将数据写入文件再进行读取
    # https://duckdb.org/docs/stable/clients/python/data_ingestion#directly-accessing-dataframes-and-arrow-objects
    file = at("scripts/_duckdbcache", f"{duck_name}.json")
    save_json(file, data)
    duckdb.sql(f"""
    CREATE TABLE {duck_name} AS
        SELECT * FROM '{file}';
    """)


def clean_duckdb_files():
    """清理duckdb的数据库文件"""
    duckdb_dir = at("scripts/_duckdbcache")
    if not os.path.exists(duckdb_dir):
        return
    for file in os.listdir(duckdb_dir):
        if file.endswith(".json"):
            os.remove(os.path.join(duckdb_dir, file))
