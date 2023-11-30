# 脚本说明

目前使用了以下脚本：

- crucible/init_crucible.py：根据 trade data 生成 assets/stats/crucible.json
- desc/stats.go：根据 desc data 生成 assets/stats/desc.json
- trade/check_gems.py： 根据 trade data 检查 assets/gems.json
- trade/check_items.py: 根据 trade data 检查 assets/*.json（除了assets/gems.json）
- tree/init_passiveskills.py：根据 tree data 生成 assets/passiveskills/*

## 初始化天赋树数据库

`tree/init_passiveskills.py`负责初始化天赋树数据库。

```bash
cd tree/
# 下载天赋树文件，然后初始化
python init_passiveskills.py

# 使用旧的天赋树文件，然后初始化
python init_passiveskills.py -ud
```