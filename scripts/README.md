# 初始化脚本
init_passiveskills.py 每个赛季天赋树变化较大，数据需要重新生成。

# diff脚本

check_gems.py 检查最新trade网站中的数据（宝石）与本地数据的差异。

check_items.py 检查最新trade网站中的数据（物品）与本地数据的差异。

# 更新脚本

pull_stats.py 通过trade网站的前后版本的增量更新，来更新本地数据库。
              也就是从理论上来讲，本地数据库对于old版本中的trade网站数据是完全匹配的。

              为了使用github的diff功能检查更新内容，pull被拆分为：update,add,del三个子命令。

replace_stats.py pull_stats.py的结果并非覆盖原文件，为了可靠性，使用该脚本进行覆盖。