import re
from common import CLIENT_GLOBAL, CLIENT_TENCENT, LANG_CHS, LANG_EN, at, is_number, read_json, save_json
from db import pair, passiveskill
from export.trade import trade_file_path

DESC_STATS_PATH = "db/stats/desc.json"
TRADE_STATS_PATH = "db/stats/trade.json"


def stat_desc_path(client: str, desc: str) -> str:
    '''获取词缀描述文件路径'''
    return at("export\\game", client, 'files', f"Metadata@StatDescriptions@{desc}.txt")


def read_stat_desc(client: str, desc: str) -> str:
    '''读取词缀描述文件'''
    file = stat_desc_path(client, desc)
    # UTF16-LE-BOM
    with open(file, 'rt', encoding='utf-16') as f:
        return f.read()


class Prop:
    def __init__(self) -> None:
        self.name = ""
        self.param_id = -1  # 参数索引，-1表示属性对应Text


NEGATIVE_INFINITY = -2147483648
POSITIVE_INFINITY = 2147483647


class ParamMatcher:
    def __init__(self) -> None:
        self.left = NEGATIVE_INFINITY
        self.right = POSITIVE_INFINITY
        self.is_not = False
        self.not_value = 0

    def is_fixed(self):
        """固定值"""
        return self.left == self.right

    def is_fixed_range(self):
        """固定范围值"""
        return NEGATIVE_INFINITY < self.left < self.right < POSITIVE_INFINITY


class Param:
    def __init__(self) -> None:
        self.matcher: ParamMatcher = ParamMatcher()
        self.Props: set[str] = set()

    def is_fixed(self):
        return self.matcher.is_fixed()

    def is_fixed_range(self):
        return self.matcher.is_fixed_range()


class Text:
    def __init__(self) -> None:
        self.params: list[Param] = []
        self.template: str = ""
        self.props: set[str] = set()

    def has_fixed_param(self):
        for param in self.params:
            if param.is_fixed():
                return True
        return False

    def fixed_range_param_count(self):
        count = 0
        for p in self.params:
            if p.is_fixed_range():
                count += 1
        return count


class Desc:
    def __init__(self) -> None:
        self.id = ""
        self.stat_ids = []
        self.texts: dict[str, list[Text]] = {}  # 根据语言索引的的文本列表


# 1: 已读取"description"
# 2: 已读取语言行
# 3: 已读取Texts行数
# 4: 已读完Texts
# 10: 遇到无效行
STATE_TAG_READED = 1
STATE_LANG_READED = 2
STAT_TEXTS_COUNT_READED = 3
STATE_TEXTS_READED = 4
STATE_ERROR = 10


class DescParser:
    def __init__(self, languages: set) -> None:
        self.descs = []
        self.state: int = STATE_TEXTS_READED
        self.curr_desc = Desc()
        self.curr_lang = ""
        self.curr_text_count = 0
        self.languages = languages

    def parse(self, lines: list[str]) -> list[Desc]:
        for (i, line) in enumerate(lines):
            line = line.strip()
            if line == "" or line.startswith("no_description") or line.startswith("include"):
                continue
            match self.state:
                case 1:
                    self.curr_desc.stat_ids = self.parse_id_line(line)
                    self.curr_desc.id = " ".join(self.curr_desc.stat_ids)
                    self.curr_lang = LANG_EN
                    self.curr_desc.texts[self.curr_lang] = []
                    self.state = STATE_LANG_READED  # 英文没有语言行，读完id行直接设置语言并跳转到STATE_LANG_READED
                case 2:
                    if line.isnumeric():
                        self.curr_text_count = int(line)
                        self.state = STAT_TEXTS_COUNT_READED
                    else:
                        self.state = 10
                case 3:
                    if self.curr_lang in self.languages:
                        text = self.parse_text(line)
                        self.curr_desc.texts[self.curr_lang].append(text)
                    self.curr_text_count -= 1
                    if self.curr_text_count == 0:
                        self.state = STATE_TEXTS_READED
                case 4:
                    if self.is_tag_line(line):
                        self.curr_desc = Desc()
                        self.descs.append(self.curr_desc)
                        self.state = STATE_TAG_READED
                    elif self.is_lang_line(line):
                        self.curr_lang = self.parse_lang(line)
                        self.curr_desc.texts[self.curr_lang] = []
                        self.state = STATE_LANG_READED
                    else:
                        self.state = STATE_ERROR
                case 10:
                    raise Exception(f"error: [stat desc] 无效行 {line}")

        return self.descs

    def is_tag_line(self, line: str) -> bool:
        return line == "description"

    def is_lang_line(self, line: str) -> bool:
        return line.startswith("lang ")

    def parse_id_line(self, line: str) -> list[str]:
        m = re.match(r"^(\d)\s+(.+)$", line)
        if m:
            return [id.strip() for id in m[2].strip().split(" ")]
        else:
            raise Exception(f"error: [stat desc] 错误的Id行 {line}")

    def parse_lang(self, line: str) -> str:
        m = re.match(r'^lang\s+"(.+)"$', line)
        if m:
            return m[1]
        else:
            raise Exception(f"error: [stat desc] 错误的语言行 {line}")

    def parse_param_matcher(self, matcher_str: str) -> ParamMatcher:
        matcher = ParamMatcher()
        if matcher_str == "#":
            pass
        elif "|" in matcher_str:
            parts = matcher_str.split("|")
            if len(parts) != 2:
                raise Exception(f"error: [stat desc] 错误的参数匹配器 {matcher_str}")
            if parts[0] == "#":
                matcher.left = NEGATIVE_INFINITY
            else:
                matcher.left = int(parts[0])
            if parts[1] == "#":
                matcher.right = POSITIVE_INFINITY
            else:
                matcher.right = int(parts[1])
        elif matcher_str.startswith("!"):
            matcher.is_not = True
            matcher.not_value = int(matcher_str[1:])
        elif is_number(matcher_str):
            value = int(matcher_str)
            matcher.left = value
            matcher.right = value
        else:
            raise Exception(f"error: [stat desc] 无效的参数匹配器 {matcher_str}")
        return matcher

    def parse_text(self, line: str) -> Text:
        text = Text()
        m = re.match(r'^(.+)\s"(.*?)"(.*)$', line)
        if m is None:
            raise Exception(f"error [stat desc] 错误的Text行 {line}")

        params_str, tmpl_str, props_str = m[1].strip(), m[2], m[3].strip()

        for matcher_str in re.split(r"\s+", params_str):
            if matcher_str == "":
                continue
            if matcher_str == "#" or "|" in matcher_str or is_number(matcher_str) or matcher_str.startswith("!"):
                param = Param()
                param.matcher = self.parse_param_matcher(matcher_str)
                text.params.append(param)
            else:
                text.props.add(matcher_str)

        text.template = self.format_template(tmpl_str)

        props = self.parse_props(props_str)
        for prop in props:
            if prop.param_id >= 0:
                text.params[prop.param_id].Props.add(prop.name)

            else:
                text.props.add(prop.name)

        return text

    def format_template(self, tmpl: str) -> str:
        # 将`\n`字符串替换为换行符
        tmpl = tmpl.replace(r"\n", "\n")

        # 将自动编号替换为显式编号
        r1 = re.compile(r"{(:[^}]+)?}")
        r2 = re.compile(r"{(\d+)(:[^}]+)?}")
        if r1.match(tmpl) and r2.match(tmpl):
            print("warning: [stat desc] 模板中同时存在自动编号和显式编号，可能导致错误", tmpl)
            return tmpl

        n = 0

        def replace(match):
            nonlocal n
            replacement = f"{{{n}{match.group(1) if match.group(1) else ''}}}"
            n += 1
            return replacement

        return re.sub(r1, replace, tmpl)

    def parse_props(self, props_str: str) -> list[Prop]:
        props: list[Prop] = []

        if props_str == "":
            return props

        on_prop = False
        for token in re.split(r"\s+", props_str):
            if token.isnumeric():
                if on_prop:
                    props[-1].param_id = int(token)-1
                else:
                    raise Exception(
                        f"error: [stat desc] 解析文本属性错误，预期属性名，而非属性索引 {props_str}")
            else:
                prop = Prop()
                prop.name = token
                props.append(prop)
                on_prop = True

        return props


def merge_descs_en_to_zh(tx_descs: list[Desc], ggg_descs: list[Desc]) -> list[Desc]:
    ggg_idx = {desc.id: desc for desc in ggg_descs}
    for desc in tx_descs:
        desc.texts[LANG_EN] = ggg_idx[desc.id].texts[LANG_EN]
        if LANG_CHS not in desc.texts:
            continue
    return tx_descs


hackable_en_stat_desc_content_entries = [
    [r'#|60 "Gain {0} Vaal Soul Per Second during effect" per_minute_to_per_second 1',
     r'60 "Gain {0} Vaal Soul Per Second during effect" per_minute_to_per_second 1'],
    [r'1|# "[DNT] Area contains {0} additional Common Chest Marker"',
     r'1 "[DNT] Area contains {0} additional Common Chest Marker"'],
    [r'10 "Freezes inflicted on you spread to Enemies within {0} metre"' + "\n",
     r'10 "Freezes inflicted on you spread to Enemies within {0} metre" locations_to_metres 1' + "\n"],
    [r'1000 "Retaliation Skills become Usable for an additional {0} second"' + "\n",
     r'1000 "Retaliation Skills become Usable for an additional {0} second" milliseconds_to_seconds_2dp_if_required 1' + "\n"],
    [r'#|-1 "{0}% increased Attack and Cast Speed  for each alive Monster in Pack" negate 1',
        r'#|-1 "{0}% increased Attack and Cast Speed for each alive Monster in Pack" negate 1']
]

hackable_zh_stat_desc_content_entries = [
    [r'#|60 "生效期间每秒获得 {0} 个瓦尔之灵" per_minute_to_per_second 1',
     r'60 "生效期间每秒获得 {0} 个瓦尔之灵" per_minute_to_per_second 1'],
    [r'#|-1 "能量护盾全满状态下防止{0:+d}%的被压制法术伤害" reminderstring ReminderTextSuppression',
     r'#|-1 "能量护盾全满状态下防止{0:+d}%的被压制法术伤害的总量" reminderstring ReminderTextSuppression'],
    [r'#|-1 "枯萎技能会使干扰持续时间延长 {0}%" negate 1',
     r'#|-1 "枯萎技能会使干扰持续时间缩短 {0}%" negate 1'],
    [r'#|-1 "【寒霜爆】技能会使减益效果的持续时间延长 {0}%" negate 1',
     r'#|-1 "【寒霜爆】技能会使减益效果的持续时间缩短 {0}%" negate 1'],
    [r'#|-1 "每 10 秒获得 {0}% 的元素伤害增益，持续 4 秒" negate 1',
     r'#|-1 "每 10 秒获得 {0}% 的元素伤害减益，持续 4 秒" negate 1'],
    [r'#|-1 "若腐化，则全域暴击率提高 {0}%" negate 1 reminderstring ReminderTextIfItemCorrupted',
     r'#|-1 "若腐化，则全域暴击率降低 {0}%" negate 1 reminderstring ReminderTextIfItemCorrupted'],
    [r'1|# "[DNT]该区域会额外出现{0}个普通宝箱标记"',
     r'1 "[DNT]该区域会额外出现{0}个普通宝箱标记"'],
    ["\t1\n\t\t# "+r'"图腾放置速度加快 {0}%"'+"\n",
     "\t2\n\t\t1|# "+r'"图腾放置速度加快 {0}%"'+"\n#|-1 "+r'"图腾放置速度减慢 {0}%"'+"\n"],
    ["\t\t1|# "+r'"若你近期内有击败敌人，则效果区域扩大 {0}%，最多 50%"'+" reminderstring ReminderTextRecently\n\t\t#|-1 "+r'"若你近期内有击败敌人，则效果区域缩小 {0}%"'+" negate 1  reminderstring ReminderTextRecently\n",
     "\t\t1|# "+r'"若你近期内有击败敌人，则效果区域扩大 {0}%，最多 50%"'+" reminderstring ReminderTextRecently\n\t\t#|-1 "+r'"若你近期内有击败敌人，则效果区域缩小 {0}%，最多 50%"'+" negate 1  reminderstring ReminderTextRecently\n"],
    [r'1 "【毒雨】可以额外发射 1 个箭矢"',
     r'1 "【毒雨】可以额外发射 {0} 个箭矢"'],
    [r'1|# "如果诅咒持续时间已经过去 25%，\n则你诅咒的敌人的移动速度被减缓 25%"',
     r'1|# "如果诅咒持续时间已经过去 25%，\n则你诅咒的敌人的移动速度被减缓 {0}%"'],
    [r'10 "对你造成的冻结会扩散给 {0} 米内的其他敌人"' + "\n",
     r'10 "对你造成的冻结会扩散给 {0} 米内的其他敌人" locations_to_metres 1' + "\n"],
    [r'1000 "反击技能的可使用时间额外延长 {0} 秒"' + "\n",
     r'1000 "反击技能的可使用时间额外延长 {0} 秒" milliseconds_to_seconds_2dp_if_required 1' + "\n"],
]


def hack_stat_desc_content(content: str, mapping: list[list[str]]):
    for entry in mapping:
        if entry[0] in content:
            content = content.replace(entry[0], entry[1])  # type: ignore
        else:
            print(f"waring: hack missed {entry[0]}")
    return content


skiped_desc_id_desc = {
    # 中文相同英文不同，是地图词缀
    "map_projectile_speed_+%",
    "map_players_gain_soul_eater_on_rare_kill_ms",
    # 中文相同英文不同，是局部词缀
    "local_gem_experience_gain_+%",
    "local_accuracy_rating_+%",
    # 中文相同英文不同，是技能说明
    "skill_range_+%",
    # 中文相同英文不同，是无效词缀
    "elemental_damage_taken_+%_during_flask_effect",
    "global_poison_on_hit",
    "bleed_on_melee_critical_strike",
    # 中文相同英文不同，但是英文均为有效词缀
    "curse_on_hit_level_warlords_mark",
    "damage_taken_+%_if_you_have_taken_a_savage_hit_recently",
    "immune_to_bleeding",
    "onslaught_buff_duration_on_kill_ms",
    # 中文相同英文不同，不知道正确词缀
    # 【断金之刃】的伤害提高，【断金之刃】的伤害降低
    "shattering_steel_damage_+%",
    "lancing_steel_damage_+%",
    # S25赛季内容的怪物词缀，与装备无关，目前存在解析bug
    "chance_%_to_convert_armour_to_chromatic_orb",
    "chance_%_to_convert_weapon_to_chaos_orb",
}

skiped_desc_id_preixes = {
    # 地图词缀
    "map_",
    "display_area_contains_",
    # 提灯
    "chance_%_to_drop_additional_",
    "chance_%_to_convert_",
    # 回忆
    "memory_line_",
    "display_memory_line_",
    # 矿坑
    "delve_biome_",
    # 赤炼玄炉插槽
    "hellscape_extra_",
}


def skip_descs(descs: list[Desc]) -> list[Desc]:
    array = []
    for d in descs:
        if LANG_CHS not in d.texts:
            continue

        if d.id in skiped_desc_id_desc:
            continue

        continue_outer = False
        for prefix in skiped_desc_id_preixes:
            if d.id.startswith(prefix):
                continue_outer = True
                break
        if continue_outer:
            continue

        # 夺宝词缀，但非回火、裁剪石效果词缀
        if "heist_" in d.id and not d.id.startswith("heist_enchantment_"):
            continue
        array.append(d)
    return array


def hack_descs(descs: list[Desc]):
    for d in descs:
        # 血影的`每个狂怒球使攻击速度减慢 4%`，应当为`每个狂怒球使攻击和施法速度减慢 4%`
        if d.id == "attack_and_cast_speed_+%_per_frenzy_charge":
            if d.texts[LANG_CHS][0].template == "每个狂怒球使攻击速度加快 {0}%":
                d.texts[LANG_CHS][0].template = "每个狂怒球使攻击和施法速度加快 {0}%"
            else:
                print(f"warning: hack missed {d.id}")
            if d.texts[LANG_CHS][1].template == "每个狂怒球使攻击速度减慢 {0}%":
                d.texts[LANG_CHS][1].template = "每个狂怒球使攻击和施法速度减慢 {0}%"
            else:
                print(f"warning: hack missed {d.id}")

        # 戴亚迪安的晨曦的`没有物理伤害`，应当为`不造成物理伤害`
        if d.id == "base_deal_no_physical_damage":
            if d.texts[LANG_CHS][0].template == "没有物理伤害":
                d.texts[LANG_CHS][0].template = "不造成物理伤害"
            else:
                print(f"warning: hack missed {d.id}")

        # 君锋镇赛季武器附魔
        if d.id == "local_elemental_damage_+%":
            if d.texts[LANG_CHS][0].template == "元素伤害提高 {0}%":
                d.texts[LANG_CHS][0].template = "该武器的元素伤害提高 {0}%"
            else:
                print(f"warning: hack missed {d.id}")
            if d.texts[LANG_CHS][1].template == "元素伤害降低 {0}%":
                d.texts[LANG_CHS][1].template = "该武器的元素伤害降低 {0}%"
            else:
                print(f"warning: hack missed {d.id}")


def fill_fixed_param_to_template(text: Text) -> str:
    """将固定值填充进模板文本"""
    tmpl = text.template
    for i, p in enumerate(text.params):
        if p.is_fixed():
            val = p.matcher.left
            if "milliseconds_to_seconds" in p.Props or "milliseconds_to_seconds_0dp" in p.Props or "milliseconds_to_seconds_2dp_if_required" in p.Props:
                val /= 1000
            elif "per_minute_to_per_second" in p.Props or "per_minute_to_per_second_2dp_if_required" in p.Props:
                val /= 60
            elif "locations_to_metres" in p.Props:
                val /= 10

            if "negate" in p.Props:
                val *= -1

            if val not in {-1, 0, 1}:
                print("waring: 填充固定参数值时遇到非{-1,0,1}值", val, text.template)
                continue

            # 上述运算可能得到一个float值，需要转换为int
            val = int(val)

            tmpl = tmpl.replace(f"{{{i}}}", f"{val}")
            tmpl = tmpl.replace(f"{{{i}:d}}", f"{val}")
            tmpl = tmpl.replace(f"{{{i}:+d}}", f"{val:+d}")
            tmpl = tmpl.replace(f"{{{i}:+}}", f"{val:+d}")
    return tmpl


def stats_of_fixed_range_params_desc(desc_id: str, zh_text: Text, en_text: Text) -> list:
    array = []

    if en_text.fixed_range_param_count() > 0:
        for i, en_param in enumerate(en_text.params):
            if en_param.is_fixed_range():
                zh_param = zh_text.params[i]
                matcher_backup = [zh_param.matcher, en_param.matcher]

                for j in range(en_param.matcher.left, en_param.matcher.right+1):
                    m1, m2 = ParamMatcher(), ParamMatcher()
                    m1.left, m2.left = j, j
                    m1.right, m2.right = j, j
                    zh_text.params[i].matcher, en_text.params[i].matcher = m1, m2
                    array.extend(stats_of_fixed_range_params_desc(
                        desc_id, zh_text, en_text))

                zh_text.params[i].matcher, en_text.params[i].matcher = matcher_backup[0], matcher_backup[1]
    else:
        array.append({"id": desc_id, "zh": fill_fixed_param_to_template(
            zh_text), "en": fill_fixed_param_to_template(en_text)})

    return array


def to_stats(descs: list[Desc]) -> list[dict]:
    array = []
    for desc in descs:
        zh_texts = desc.texts[LANG_CHS]
        en_texts = desc.texts[LANG_EN]
        if len(zh_texts) != len(en_texts):
            print("warning: [stat desc] 中英文文本数量不匹配", desc.id)

        for i, zh_text in enumerate(zh_texts):
            if zh_text.template.isascii():
                continue

            en_text = en_texts[i]

            nextSameZhIndex = -1
            for j in range(i+1, len(zh_texts)):
                if zh_text.template == zh_texts[j].template:
                    nextSameZhIndex = j
                    break

            # 对中文模板相同，但英文模板不同的情况进行特殊处理
            # 常见于英文复数名称区别于单数的情况
            if nextSameZhIndex > 0:
                if en_text.template == en_texts[nextSameZhIndex].template:
                    continue

                if len(en_text.params) == 0:
                    print("warning: [stat desc] 英文文本的参数个数为0", desc.id)
                    continue

                # 目前出现这种特殊情况只有一个原因：因为单复数的英文表示法不同于中文
                # 所有我们首先处理存在固定参数值Text
                if en_text.has_fixed_param():
                    array.append(
                        {"id": desc.id, "zh": fill_fixed_param_to_template(zh_text), "en": fill_fixed_param_to_template(en_text)})
                # 唯一一个特例是“local_maximum_prefixes_allowed_+”和“local_maximum_suffixes_allowed_+”
                # 多大师词缀：-1|1 "允许的前缀 {0:+d}"   -1|1 "允许的后缀 {0:+d}"
                # 它是范围参数值，但也是因为单复数的英文表示法不同于中文导致的
                elif en_text.fixed_range_param_count() > 0:
                    array.extend(stats_of_fixed_range_params_desc(
                        desc.id, zh_text, en_text))
                else:
                    print(
                        "warning: [stat desc] unreachable branch", desc.id)
                continue

            array.append(
                {"id": desc.id, "zh": zh_text.template, "en": en_text.template})

    return array


random_indexable_support_desc_ids = ["local_random_support_gem_level local_random_support_gem_index",
                                     "local_random_support_gem_level_1 local_random_support_gem_index_1"]

random_indexable_skill_desc_ids = [
    "random_skill_gem_level_+_level random_skill_gem_level_+_index"]

random_passive_desc_ids = [
    "local_unique_jewel_disconnected_passives_can_be_allocated_around_keystone_hash"
]


def append_random_reference_stats(stats: list) -> list:
    """添加包含其它引用的词缀
    未来有更好的处理方式，但目前没时间重构
    """
    array = []
    for stat in stats:
        if stat["id"] in random_indexable_support_desc_ids:
            if not stat["zh"] == "插入的技能石被 {0} 级的【{1}】辅助" and stat["en"] == "Socketed Gems are Supported by Level {0} {1}":
                raise Exception("辅助宝石词缀模板已改变，请更新脚本")
        elif stat["id"] in random_indexable_skill_desc_ids:
            if not (stat["zh"] == "所有 {1} 宝石等级 +{0}" and stat["en"] == "+{0} to Level of all {1} Gems" or
                    stat["zh"] == "所有 {1} 宝石等级 -{0}" and stat["en"] == "-{0} to Level of all {1} Gems"):
                raise Exception("技能宝石词缀模板已改变，请更新脚本")
        elif stat["id"] in random_passive_desc_ids:
            if not stat["zh"] == "{0}范围内的核心天赋技能可以在\n未连结至天赋树的情况下配置\n通途" and \
                    stat["en"] == "Passive Skills in Radius of {0} can be Allocated\nwithout being connected to your tree\nPassage":
                raise Exception("天赋树节点词缀模板已改变，请更新脚本")
        else:
            array.append(stat)

    indexable_support_gems = pair.select_pairs(
        "IndexableSupportGems,Index,Name")
    for gem in indexable_support_gems:
        zh = gem["zh"]
        en = gem["en"]
        array.append(
            {"id": random_indexable_support_desc_ids[0],
             "zh": f"插入的技能石被 {{0}} 级的【{zh}】辅助",
             "en": f"Socketed Gems are Supported by Level {{0}} {en}"})

    indexable_skill_gems = pair.select_pairs(
        "IndexableSkillGems,Index,Name1")
    for gem in indexable_skill_gems:
        zh = gem["zh"]
        en = gem["en"]
        array.append(
            {"id": random_indexable_skill_desc_ids[0],
             "zh": f"所有 {zh} 宝石等级 +{{0}}",
             "en": f"+{{0}} to Level of all {en} Gems"})
        array.append(
            {"id": random_indexable_skill_desc_ids[0],
             "zh": f"所有 {zh} 宝石等级 -{{0}}",
             "en": f"-{{0}} to Level of all {en} Gems"})

    keystones = read_json(at(passiveskill.KEYSTONES_PATH))
    for keystone in keystones:
        zh = keystone["zh"]
        en = keystone["en"]
        array.append(
            {"id": random_indexable_support_desc_ids[0],
             "zh": f"{zh}范围内的核心天赋技能可以在\n未连结至天赋树的情况下配置\n通途",
             "en": f"Passive Skills in Radius of {en} can be Allocated\nwithout being connected to your tree\nPassage"})
    return array


def relocate_param_num(stat: dict):
    zh_param_nums = {int(n) for n in re.findall(r'\{(\d+)\}', stat["zh"])}
    en_param_nums = {int(n) for n in re.findall(r'\{(\d+)\}', stat["en"])}

    if len(en_param_nums-zh_param_nums) > 0:
        print("warning: 中文模板缺失形式参数", stat["id"])
        print(stat["zh"])
        print(stat["en"])
        return

    if len(zh_param_nums) == 0:
        return

    num_list = list(zh_param_nums)
    num_list.sort()
    if num_list[-1] == len(zh_param_nums)-1:
        return

    for new_num, num in enumerate(num_list):
        stat["zh"] = stat["zh"].replace(f"{{{num}}}", f"{{{new_num}}}")
        stat["en"] = stat["en"].replace(f"{{{num}}}", f"{{{new_num}}}")


def format_stat(stat: dict):
    pattern = r'\{(\d+):\+?d\}'
    stat["en"] = re.sub(pattern, r'{\1}', stat["en"])
    stat["zh"] = re.sub(pattern, r'{\1}', stat["zh"])
    relocate_param_num(stat)


def load_descs(name: str, hack_content=False, hack_tables=[]) -> list[Desc]:
    global_desc_content = read_stat_desc(CLIENT_GLOBAL, name)
    tencent_desc_content = read_stat_desc(CLIENT_TENCENT, name)

    if hack_content:
        global_desc_content = hack_stat_desc_content(
            global_desc_content, hack_tables[0])
        tencent_desc_content = hack_stat_desc_content(
            tencent_desc_content, hack_tables[1])

    global_basic_descs = DescParser({LANG_EN}).parse(
        global_desc_content.splitlines())
    tencent_basic_descs = DescParser({LANG_CHS}).parse(
        tencent_desc_content.splitlines())

    descs = merge_descs_en_to_zh(tencent_basic_descs, global_basic_descs)

    return descs


def create_game_stats():
    print(f"info: 创建 {DESC_STATS_PATH} ...")

    basic_descs = load_descs("stat_descriptions", hack_content=True, hack_tables=[
        hackable_en_stat_desc_content_entries, hackable_zh_stat_desc_content_entries])
    tincture_desc = load_descs("tincture_stat_descriptions")
    basic_descs.extend(tincture_desc)

    descs = skip_descs(basic_descs)
    hack_descs(descs)

    array = to_stats(descs)
    array = append_random_reference_stats(array)

    for stat in array:
        format_stat(stat)

    save_json(at(DESC_STATS_PATH), array)


def get_stats_from_trade_data(data, group_id_label_filter: set):
    stats = []
    result = data["result"]
    for group in result:
        id = group["id"]
        if group_id_label_filter is not None and id not in group_id_label_filter:
            continue

        entries = group["entries"]
        for entry in entries:
            stats.append(entry)
    return stats


small_passive_skill_option_suffix_legacy = " (Legacy)"
tx_small_passive_skill_option_suffix_legacy = " (遗产)"


def create_small_passive_skills_stats():
    print(f"info: 创建 {TRADE_STATS_PATH} ...")
    global_stats = read_json(trade_file_path(CLIENT_GLOBAL, "stats.json"))
    tencent_stats = read_json(trade_file_path(CLIENT_TENCENT, "stats.json"))

    group_label = "enchant"

    global_stats = get_stats_from_trade_data(global_stats, set([group_label]))
    tencent_stats = get_stats_from_trade_data(
        tencent_stats, set([group_label]))

    tx_stats_idx = {}
    for item in tencent_stats:
        id = item["id"]
        tx_stats_idx[id] = item

    small_passive_skills_stat = {}
    tx_small_passive_skills_stat = {}

    for item in global_stats:
        id = item["id"]
        text: str = item["text"]

        if text == "Added Small Passive Skills grant: #":
            small_passive_skills_stat = item
            tx_small_passive_skills_stat = tx_stats_idx[id]
            break

    spread_stats = []
    spread_stats_idx = {}
    small_passive_skills_stat_id: str = small_passive_skills_stat["id"]
    if small_passive_skills_stat_id.startswith(group_label+"."):
        small_passive_skills_stat_id = small_passive_skills_stat_id[len(
            group_label)+1:]

    for option in small_passive_skills_stat["option"]["options"]:
        id = option["id"]
        text: str = option["text"]

        if text.endswith(small_passive_skill_option_suffix_legacy):
            text = text[:len(
                text)-len(small_passive_skill_option_suffix_legacy)]

        stat = {}
        stat["id"] = f"{small_passive_skills_stat_id}_{id}"

        if "\n" in text:
            zh_pieces = []
            pieces = text.split("\n")
            for piece in pieces:
                zh_pieces.append(
                    small_passive_skills_stat["text"].replace("#", piece))
            stat["en"] = "\n".join(zh_pieces)
        else:
            stat["en"] = small_passive_skills_stat["text"].replace("#", text)

        spread_stats.append(stat)
        spread_stats_idx[stat["id"]] = stat

    for option in tx_small_passive_skills_stat["option"]["options"]:
        id = option["id"]
        text: str = option["text"]

        if text.endswith(tx_small_passive_skill_option_suffix_legacy):
            text = text[:len(
                text)-len(tx_small_passive_skill_option_suffix_legacy)]

        stat = spread_stats_idx[f"{small_passive_skills_stat_id}_{id}"]

        if "\n" in text:
            zh_pieces = []
            pieces = text.split("\n")
            for piece in pieces:
                zh_pieces.append(
                    tx_small_passive_skills_stat["text"].replace("#", piece))
            stat["zh"] = "\n".join(zh_pieces)
        else:
            stat["zh"] = tx_small_passive_skills_stat["text"].replace(
                "#", text)

    for (i, stat) in enumerate(spread_stats):
        spread_stats[i] = {"id": stat["id"],
                           "zh": stat["zh"], "en": stat["en"]}

    save_json(at("db/stats/trade.json"), spread_stats)


def create_stats():
    create_game_stats()
    create_small_passive_skills_stats()
