# PT Sites Clash Rules (PT站 Clash 分流规则)

[![GitHub stars](https://img.shields.io/github/stars/Zeeshan975/Clash_rules?style=social)](https://github.com/Zeeshan975/Clash_rules)
[![Total Sites](https://img.shields.io/badge/Total%20Sites-342-brightgreen.svg)](https://github.com/Zeeshan975/Clash_rules)
[![Active Sites](https://img.shields.io/badge/Active%20Sites-257-blue.svg)](https://github.com/Zeeshan975/Clash_rules)
[![Rules](https://img.shields.io/badge/Clash%20Rules-326%20Domains-orange.svg)](https://github.com/Zeeshan975/Clash_rules)
[![Auto Update](https://img.shields.io/badge/Auto%20Update-Daily-blueviolet.svg)](https://github.com/Zeeshan975/Clash_rules/actions)

本项目自动提取自 **[PT-depiler](https://github.com/pt-plugins/PT-depiler)**（PT 站点助手聚合项目）官方站点数据库中的所有 PT/BT 网站地址与域名，针对 Clash / Clash Meta (Mihomo) / OpenClash / Clash Verge / Clash Nyanpasu / Surge / Quantumult X 等客户端生成精确的规则集。

---

## 📊 站点统计

| 类别 | 站点数量 | 域名规则数 | 说明 |
| :--- | :---: | :---: | :--- |
| **全量活跃站点 (`PT`)** | **257** | **326** | 包含所有正常运营的私有 PT 与公开 BT 站点（推荐） |
| **私有 PT 站 (`PT_Private`)** | **242** | **286** | 仅包含私有 PT 站点（推荐绑定直连 `DIRECT`，防止跳 IP 封号） |
| **公开 BT 站 (`PT_Public`)** | **15** | **40** | 包含 1337x, Nyaa, E-Hentai, ACG.RIP 等公开 BT 索引站 |
| **归档全量库 (`PT_All`)** | **342** | **493** | 包含历史曾用域名及已关闭的站点 (85 个已关站) |

---

## 🚀 规则订阅链接

### 1. 经典 Rule-Provider (YAML 格式，推荐 Clash / Clash Meta / Mihomo)

| 规则名称 | GitHub Raw 直链 | jsDelivr CDN 加速链接 |
| :--- | :--- | :--- |
| **全量活跃 (`PT.yaml`)** | `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT.yaml` | `https://cdn.jsdelivr.net/gh/Zeeshan975/Clash_rules@main/rules/PT.yaml` |
| **私有 PT 站 (`PT_Private.yaml`)** | `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT_Private.yaml` | `https://cdn.jsdelivr.net/gh/Zeeshan975/Clash_rules@main/rules/PT_Private.yaml` |
| **公开 BT 站 (`PT_Public.yaml`)** | `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT_Public.yaml` | `https://cdn.jsdelivr.net/gh/Zeeshan975/Clash_rules@main/rules/PT_Public.yaml` |
| **归档全量 (`PT_All.yaml`)** | `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT_All.yaml` | `https://cdn.jsdelivr.net/gh/Zeeshan975/Clash_rules@main/rules/PT_All.yaml` |

> 根目录也提供了顶层快捷订阅：`https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/PT.yaml`

### 2. 文本列表格式 (`.list` / `.rules`)

适用于 Subconverter 订阅转换器、Quantumult X、Surge 等：

- `PT.list`: `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT.list`
- `PT_Private.list`: `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT_Private.list`

### 3. Domain 模式 Rule-Provider (`+.domain.com`)

- `PT_Domain.yaml`: `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT_Domain.yaml`
- `PT_Private_Domain.yaml`: `https://raw.githubusercontent.com/Zeeshan975/Clash_rules/main/rules/PT_Private_Domain.yaml`

---

## 🛠️ Clash 配置示例

### 场景 A：私有 PT 站直连（防跳 IP / 刷流保种推荐）

在 Clash / Clash Meta / Mihomo 配置文件中加入：

```yaml
rule-providers:
  PT_Private:
    type: http
    behavior: classical
    url: "https://cdn.jsdelivr.net/gh/Zeeshan975/Clash_rules@main/rules/PT_Private.yaml"
    path: ./ruleset/PT_Private.yaml
    interval: 86400

rules:
  - RULE-SET,PT_Private,DIRECT
  # 其他代理规则...
```

### 场景 B：全量 PT 走独立策略组（如指定原生 IP 节点）

```yaml
proxy-groups:
  - name: 🎯 PT专用
    type: select
    proxies:
      - DIRECT
      - 🇭🇰 香港原生节点
      - 🇯🇵 日本家宽节点

rule-providers:
  PT:
    type: http
    behavior: classical
    url: "https://cdn.jsdelivr.net/gh/Zeeshan975/Clash_rules@main/rules/PT.yaml"
    path: ./ruleset/PT.yaml
    interval: 86400

rules:
  - RULE-SET,PT,🎯 PT专用
  # 其他常规规则...
```

---

## 📋 部分精选支持站点

<details>
<summary><b>点击展开查看部分涵盖的知名 PT 站点名单</b></summary>

- **综合大站 / 知名站点**：M-Team (馒头), CHDBits, OpenCD, TTG, HDChina, FRDS (朋友), SpringSunday (春天), HDSky (天空), Ourbits (我堡), BTSCHOOL (学校), SSD, Putao (葡萄), BYR (北邮), TJUPT (北洋), U2 (动漫花园娘家), HDRoute (路由), LemonHD (柠檬), HDHome (家园), PTTime (时间), Audiences, RedLeaves (红叶), HDTime, HDFans, JoyHD, CarPT, NicePT, HaiDan (海胆), Discfan, SharkPT, TangPT, AgsvPT, Kufei, PandaPT 等
- **外站 / 国际著名站点**：PTP (PassThePopcorn), RED (Redacted), GazelleGames (GGn), TorrentLeech, BTN (BroadcastheNet), AnimeBytes, Bibliotik, Empornium, MAM (MyAnonaMouse), IPTorrents, FileList, UHDBits, HDBits, CinemaZ, AvistaZ, AsianCinema, Beyond-HD, CRT, CGPeers, SugoiMusic 等
- **公开 BT 站 / 索引站**：1337x, Nyaa, ACG.RIP, AnimeTosho, AniRena, E-Hentai, Tokyo Toshokan 等

完整站点数据可查阅 [`data/sites.json`](data/sites.json)。
</details>

---

## 🔄 自动化更新机制

- 本仓库内置 GitHub Actions 自动更新工作流 (`.github/workflows/update.yml`)。
- 每天定时拉取 [PT-depiler](https://github.com/pt-plugins/PT-depiler) 的最新站点代码，自动解码 ROT13 加密网址、智能解析多级根域名并同步生成所有规则文件。
- 本地手动更新：
  ```bash
  python scripts/generate.py
  ```

---

## ⚖️ 免责声明

1. 本规则集仅收录域名及网络路由规则，不存储任何种子文件、资源或数据。
2. 规则中的网站地址均收集自开源社区项目，遵守各站点相关使用准则。
