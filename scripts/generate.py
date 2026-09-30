#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash Rules Generator for PT (Private Tracker) Sites
Source: https://github.com/pt-plugins/PT-depiler
Repository: https://github.com/Zeeshan975/Clash_rules
"""

import os
import re
import sys
import json
import shutil
import tempfile
import subprocess
from datetime import datetime
from urllib.parse import urlparse

# Shared or public multi-tenant root domains that MUST NOT be stripped to root
# to avoid affecting unrelated subdomains or services.
SHARED_DOMAINS = {
    # Academic & University Networks
    'edu.cn', 'bjtu.edu.cn', 'hust.edu.cn', 'neu6.edu.cn', 'nwsuaf6.edu.cn',
    'sjtu.edu.cn', 'xauat6.edu.cn', 'xidian.edu.cn', 'byr.cn',
    # Free DDNS / Subdomain Registries
    'eu.org', 'pp.ua', 'us.kg', 'dpdns.org', 'leniter.org',
    # Community & Mirror Hosts
    'itzmx.com', 'eastgame.org', 'etree.org', 'kelu.one', 'dmhy.org',
    # Public Mirror / Unblock Proxies
    'abcproxy.org', 'mrunblock.bond', 'ninjaproxy1.com', 'proxyninja.net',
    'proxyninja.org', 'torrentbay.st', 'torrentsbay.org', 'unblockit.download', 'unblockninja.com',
}

TWO_LEVEL_TLDS = [
    'edu.cn', 'com.cn', 'org.cn', 'gov.cn', 'net.cn',
    'co.uk', 'org.uk', 'me.uk', 'com.au', 'net.au', 'co.nz'
]

def rot13(s: str) -> str:
    lookup = {}
    for i in range(26):
        c1 = chr(ord('a') + i)
        c2 = chr(ord('a') + (i + 13) % 26)
        lookup[c1] = c2
        lookup[c1.upper()] = c2.upper()
    return ''.join(lookup.get(c, c) for c in s)

def decode_url(u: str) -> str:
    u = u.strip().strip("'\"")
    if u.startswith('uggc'):
        return rot13(u)
    return u

def strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        parts = re.split(r'(?<!:)\s*//.*$', line)
        lines.append(parts[0])
    return '\n'.join(lines)

def parse_array(block_text: str) -> list:
    cleaned = strip_comments(block_text)
    raw = re.findall(r'["\']([^"\']+)["\']', cleaned)
    return [decode_url(x) for x in raw]

def extract_site_metadata_block(content: str) -> str:
    """Extract strictly the siteMetadata object block to avoid matching variables defined elsewhere."""
    m = re.search(r'(?:export\s+)?const\s+siteMetadata\s*(?::\s*[^=]+)?\s*=\s*\{', content)
    if not m:
        return ""
    start_idx = m.end() - 1  # at the opening '{'
    brace_depth = 0
    in_single_quote = False
    in_double_quote = False
    in_template_lit = False
    in_line_comment = False
    in_block_comment = False
    i = start_idx
    length = len(content)

    while i < length:
        char = content[i]
        if in_line_comment:
            if char == '\n':
                in_line_comment = False
        elif in_block_comment:
            if char == '*' and i + 1 < length and content[i+1] == '/':
                in_block_comment = False
                i += 1
        elif in_single_quote:
            if char == '\\':
                i += 1
            elif char == "'":
                in_single_quote = False
        elif in_double_quote:
            if char == '\\':
                i += 1
            elif char == '"':
                in_double_quote = False
        elif in_template_lit:
            if char == '\\':
                i += 1
            elif char == '`':
                in_template_lit = False
        else:
            if char == '/' and i + 1 < length and content[i+1] == '/':
                in_line_comment = True
                i += 1
            elif char == '/' and i + 1 < length and content[i+1] == '*':
                in_block_comment = True
                i += 1
            elif char == "'":
                in_single_quote = True
            elif char == '"':
                in_double_quote = True
            elif char == '`':
                in_template_lit = True
            elif char == '{':
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    return content[start_idx:i+1]
        i += 1
    return content[start_idx:]

def extract_rule_domain(host: str) -> str:
    host = host.lower().strip()
    if not host:
        return ""
    if host.startswith('www.'):
        clean_host = host[4:]
    else:
        clean_host = host

    # Check shared / multi-tenant domains
    for sd in sorted(SHARED_DOMAINS, key=len, reverse=True):
        if clean_host.endswith('.' + sd):
            prefix = clean_host[:-len(sd)-1]
            sub = prefix.split('.')[-1]
            return f"{sub}.{sd}"
        elif clean_host == sd:
            return sd

    # Check two-level TLDs
    matched_tld = None
    for tld in TWO_LEVEL_TLDS:
        if clean_host.endswith('.' + tld):
            matched_tld = tld
            break

    parts = clean_host.split('.')
    if matched_tld:
        if len(parts) >= 3:
            return '.'.join(parts[-3:])
        return clean_host
    else:
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return clean_host

def parse_definitions(definitions_dir: str):
    sites = []
    for fname in sorted(os.listdir(definitions_dir)):
        if not fname.endswith('.ts'):
            continue
        site_id = fname[:-3]
        fpath = os.path.join(definitions_dir, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        block = extract_site_metadata_block(content)
        if not block:
            block = content

        m_urls = re.search(r'urls\s*:\s*\[(.*?)\]', block, re.DOTALL)
        urls = parse_array(m_urls.group(1)) if m_urls else []

        m_legacy = re.search(r'legacyUrls\s*:\s*\[(.*?)\]', block, re.DOTALL)
        legacy_urls = parse_array(m_legacy.group(1)) if m_legacy else []

        m_name = re.search(r'name\s*:\s*["\']([^"\']+)["\']', block)
        name = m_name.group(1) if m_name else site_id

        m_aka = re.search(r'aka\s*:\s*\[(.*?)\]', block, re.DOTALL)
        aka = parse_array(m_aka.group(1)) if m_aka else []

        m_desc = re.search(r'description\s*:\s*["\']([^"\']+)["\']', block)
        desc = m_desc.group(1) if m_desc else ""

        m_tags = re.search(r'tags\s*:\s*\[(.*?)\]', block, re.DOTALL)
        tags = parse_array(m_tags.group(1)) if m_tags else []

        m_type = re.search(r'type\s*:\s*["\']([^"\']+)["\']', block)
        stype = m_type.group(1) if m_type else "private"

        m_schema = re.search(r'schema\s*:\s*["\']([^"\']+)["\']', block)
        schema = m_schema.group(1) if m_schema else ""

        is_dead = bool(re.search(r'isDead\s*:\s*true', block))

        # Extract domains
        active_domains = set()
        for u in urls:
            p = urlparse(u)
            h = (p.netloc or p.path).lower().split(':')[0].strip()
            if h:
                rd = extract_rule_domain(h)
                if rd:
                    active_domains.add(rd)

        all_domains = set(active_domains)
        for u in legacy_urls:
            p = urlparse(u)
            h = (p.netloc or p.path).lower().split(':')[0].strip()
            if h:
                rd = extract_rule_domain(h)
                if rd:
                    all_domains.add(rd)

        sites.append({
            'id': site_id,
            'name': name,
            'aka': aka,
            'description': desc,
            'tags': tags,
            'type': stype,
            'schema': schema,
            'isDead': is_dead,
            'urls': urls,
            'legacyUrls': legacy_urls,
            'activeDomains': sorted(list(active_domains)),
            'allDomains': sorted(list(all_domains))
        })

    return sites

def generate_rules(sites, output_dir):
    os.makedirs(os.path.join(output_dir, 'rules'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'data'), exist_ok=True)

    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    categories = {
        'PT': {
            'title': 'PT Sites & Trackers (Active Private & Public)',
            'desc': 'All active PT/BT sites and tracker domains',
            'sites': [s for s in sites if not s['isDead']],
            'use_all_domains': False
        },
        'PT_Private': {
            'title': 'Private PT Trackers (Strictly Private Sites)',
            'desc': 'Active private tracker sites only (recommended for DIRECT routing)',
            'sites': [s for s in sites if not s['isDead'] and s['type'] == 'private'],
            'use_all_domains': False
        },
        'PT_Public': {
            'title': 'Public BT & Torrent Indexers',
            'desc': 'Public torrent search and tracker sites (e.g. 1337x, Nyaa, E-Hentai)',
            'sites': [s for s in sites if not s['isDead'] and s['type'] == 'public'],
            'use_all_domains': False
        },
        'PT_All': {
            'title': 'All PT/BT Domains (Including Legacy & Archived Sites)',
            'desc': 'Comprehensive archive including historical domains and defunct sites',
            'sites': sites,
            'use_all_domains': True
        }
    }

    stats = {}

    for cat_name, cat_info in categories.items():
        domain_to_sites = {}
        for s in cat_info['sites']:
            d_list = s['allDomains'] if cat_info['use_all_domains'] else s['activeDomains']
            for d in d_list:
                domain_to_sites.setdefault(d, []).append(s['name'])

        sorted_domains = sorted(domain_to_sites.keys())
        stats[cat_name] = {
            'site_count': len(cat_info['sites']),
            'domain_count': len(sorted_domains)
        }

        # 1. Classical Rule Provider YAML (rules/{cat_name}.yaml)
        yaml_lines = [
            f"# {cat_info['title']}",
            f"# Description: {cat_info['desc']}",
            f"# Updated: {now_str}",
            f"# Total Rules: {len(sorted_domains)}",
            f"# Source: https://github.com/pt-plugins/PT-depiler",
            f"# Repo: https://github.com/Zeeshan975/Clash_rules",
            "#",
            "payload:"
        ]
        for d in sorted_domains:
            # deduplicate site names in comment
            names = list(dict.fromkeys(domain_to_sites[d]))
            names_str = ', '.join(names[:3])
            yaml_lines.append(f"  - DOMAIN-SUFFIX,{d} # {names_str}")

        yaml_content = '\n'.join(yaml_lines) + '\n'
        with open(os.path.join(output_dir, 'rules', f'{cat_name}.yaml'), 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        # 2. Text Rule List (rules/{cat_name}.list)
        list_lines = [
            f"# {cat_info['title']}",
            f"# Description: {cat_info['desc']}",
            f"# Updated: {now_str}",
            f"# Total Rules: {len(sorted_domains)}",
            f"# Source: https://github.com/pt-plugins/PT-depiler",
            f"# Repo: https://github.com/Zeeshan975/Clash_rules",
            "#"
        ]
        for d in sorted_domains:
            names = list(dict.fromkeys(domain_to_sites[d]))
            names_str = ', '.join(names[:3])
            list_lines.append(f"DOMAIN-SUFFIX,{d} # {names_str}")

        list_content = '\n'.join(list_lines) + '\n'
        with open(os.path.join(output_dir, 'rules', f'{cat_name}.list'), 'w', encoding='utf-8') as f:
            f.write(list_content)

        # 3. Domain Rule Provider YAML (rules/{cat_name}_Domain.yaml)
        domain_yaml_lines = [
            f"# {cat_info['title']} (Domain Provider Format)",
            f"# Description: {cat_info['desc']}",
            f"# Updated: {now_str}",
            f"# Total Domains: {len(sorted_domains)}",
            f"# Source: https://github.com/pt-plugins/PT-depiler",
            f"# Repo: https://github.com/Zeeshan975/Clash_rules",
            "#",
            "payload:"
        ]
        for d in sorted_domains:
            names = list(dict.fromkeys(domain_to_sites[d]))
            names_str = ', '.join(names[:3])
            domain_yaml_lines.append(f"  - '+.{d}' # {names_str}")

        domain_yaml_content = '\n'.join(domain_yaml_lines) + '\n'
        with open(os.path.join(output_dir, 'rules', f'{cat_name}_Domain.yaml'), 'w', encoding='utf-8') as f:
            f.write(domain_yaml_content)

        # Also copy primary PT.yaml and PT.list to repository root for convenient top-level raw URLs
        if cat_name == 'PT':
            with open(os.path.join(output_dir, 'PT.yaml'), 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            with open(os.path.join(output_dir, 'PT.list'), 'w', encoding='utf-8') as f:
                f.write(list_content)
            with open(os.path.join(output_dir, 'PT_Domain.yaml'), 'w', encoding='utf-8') as f:
                f.write(domain_yaml_content)

    # Save structured sites.json
    with open(os.path.join(output_dir, 'data', 'sites.json'), 'w', encoding='utf-8') as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)

    return stats

def update_readme(output_dir, sites, stats):
    active_sites = [s for s in sites if not s['isDead']]
    private_sites = [s for s in active_sites if s['type'] == 'private']
    public_sites = [s for s in active_sites if s['type'] == 'public']
    dead_sites = [s for s in sites if s['isDead']]

    readme_content = f"""# PT Sites Clash Rules (PT站 Clash 分流规则)

[![GitHub stars](https://img.shields.io/github/stars/Zeeshan975/Clash_rules?style=social)](https://github.com/Zeeshan975/Clash_rules)
[![Total Sites](https://img.shields.io/badge/Total%20Sites-{len(sites)}-brightgreen.svg)](https://github.com/Zeeshan975/Clash_rules)
[![Active Sites](https://img.shields.io/badge/Active%20Sites-{len(active_sites)}-blue.svg)](https://github.com/Zeeshan975/Clash_rules)
[![Rules](https://img.shields.io/badge/Clash%20Rules-{stats['PT']['domain_count']}%20Domains-orange.svg)](https://github.com/Zeeshan975/Clash_rules)
[![Auto Update](https://img.shields.io/badge/Auto%20Update-Daily-blueviolet.svg)](https://github.com/Zeeshan975/Clash_rules/actions)

本项目自动提取自 **[PT-depiler](https://github.com/pt-plugins/PT-depiler)**（PT 站点助手聚合项目）官方站点数据库中的所有 PT/BT 网站地址与域名，针对 Clash / Clash Meta (Mihomo) / OpenClash / Clash Verge / Clash Nyanpasu / Surge / Quantumult X 等客户端生成精确的规则集。

---

## 📊 站点统计

| 类别 | 站点数量 | 域名规则数 | 说明 |
| :--- | :---: | :---: | :--- |
| **全量活跃站点 (`PT`)** | **{stats['PT']['site_count']}** | **{stats['PT']['domain_count']}** | 包含所有正常运营的私有 PT 与公开 BT 站点（推荐） |
| **私有 PT 站 (`PT_Private`)** | **{stats['PT_Private']['site_count']}** | **{stats['PT_Private']['domain_count']}** | 仅包含私有 PT 站点（推荐绑定直连 `DIRECT`，防止跳 IP 封号） |
| **公开 BT 站 (`PT_Public`)** | **{stats['PT_Public']['site_count']}** | **{stats['PT_Public']['domain_count']}** | 包含 1337x, Nyaa, E-Hentai, ACG.RIP 等公开 BT 索引站 |
| **归档全量库 (`PT_All`)** | **{stats['PT_All']['site_count']}** | **{stats['PT_All']['domain_count']}** | 包含历史曾用域名及已关闭的站点 ({len(dead_sites)} 个已关站) |

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
"""
    with open(os.path.join(output_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_content)

def main():
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Check if local PT-depiler path provided as argument or exists in scratch
    pt_depiler_dir = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        pt_depiler_dir = sys.argv[1]
    else:
        scratch_path = r"C:\Users\10067\.gemini\antigravity\brain\6200d547-3eef-4926-9410-5e2ec1ad5aa0\scratch\pt-depiler"
        if os.path.exists(scratch_path):
            pt_depiler_dir = scratch_path

    temp_clone_dir = None
    if not pt_depiler_dir:
        temp_clone_dir = tempfile.mkdtemp(prefix='pt_depiler_')
        print(f"Cloning https://github.com/pt-plugins/PT-depiler.git into {temp_clone_dir}...")
        subprocess.run(['git', 'clone', '--depth', '1', 'https://github.com/pt-plugins/PT-depiler.git', temp_clone_dir], check=True)
        pt_depiler_dir = temp_clone_dir

    definitions_dir = os.path.join(pt_depiler_dir, 'src', 'packages', 'site', 'definitions')
    if not os.path.exists(definitions_dir):
        print(f"Error: definitions directory not found at {definitions_dir}")
        sys.exit(1)

    print(f"Parsing definitions from {definitions_dir}...")
    sites = parse_definitions(definitions_dir)
    print(f"Parsed {len(sites)} sites.")

    print(f"Generating Clash rules in {repo_dir}...")
    stats = generate_rules(sites, repo_dir)

    print("Updating README.md...")
    update_readme(repo_dir, sites, stats)

    if temp_clone_dir and os.path.exists(temp_clone_dir):
        shutil.rmtree(temp_clone_dir, ignore_errors=True)

    print("\nGeneration completed successfully!")
    for k, v in stats.items():
        print(f"  [{k:12}] Sites: {v['site_count']:3} | Domains: {v['domain_count']:3}")

if __name__ == '__main__':
    main()
