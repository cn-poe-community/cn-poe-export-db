# 归档

⚠️本项目已经被[cn-poe-utils](https://github.com/cn-poe-community/cn-poe-utils)取代。

# cn-poe-export-db

PoExport项目的数据库。

# usage

## javascript

作为iife使用（如果版本更新，请将版本号替换为最新版本）：

```html
<script src="https://unpkg.com/cn-poe-export-db@0.0.7/dist/db.global.js"></script>
<script>
const {gems} = CnPoeExportDb;
//...
</script>
```

作为esm模块使用，安装：

```
npm install cn-poe-export-db --save
```

代码：

```js
import CnPoeExportDb from cn-poe-export-db;
const {gems} = CnPoeExportDb;
//...
```

# 已知问题

存在一些中文的翻译问题，需要客户端修复。

## 物品

存在一些同名的中文基底物品：`召集法杖`,`龙骨细剑`,`丝绸手套`,`丝绒手套`，翻译难度较大。

## 升华

贵族与刺客存在重复的`暗影`升华，受影响的物品包括`禁断之肉`、`禁断之火`，数据库将贵族版本修正为`暗影（贵族）`，需要前端hack。

## 涂油

存在一些重复的天赋大点名称，与之相关的涂油词缀无法翻译。

## 词缀

存在以下中文翻译错误：

- 重复的`没有物理伤害`，戴亚迪安的晨曦，武器的异度天灾赛季词缀应当为`不造成物理伤害`，数据库已修正，需要前端hack
- 重复的`【断金之刃】的伤害提高`，`【断金之刃】的伤害降低`，其中一个应当是`破碎铁刃...`，无法区分
- 重复的`每个狂怒球使攻击速度减慢 4%`，血影上的应当为`每个狂怒球使攻击和施法速度减慢 4%`，数据库已修正，需要前端hack
- 重复的`元素伤害提高`，`元素伤害降低`，君锋镇赛季的武器附魔应当为`该武器的元素伤害...`，数据库已经修正，需要前端hack

# credits

[poe-dat-viewer](https://github.com/SnosMe/poe-dat-viewer)<br/>
[dat-schema](https://github.com/poe-tool-dev/dat-schema)
