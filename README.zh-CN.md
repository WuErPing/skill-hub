# skill-hub

<p align="center"><img src="docs/assets/icon.svg" width="120" alt="skill-hub logo"></p>

**[English](./README.md)** | **[中文](./README.zh-CN.md)**

基于 Web UI 的 GitHub 仓库和本地目录技能管理工具 — 核心目标是**减少不必要的 Token 开销**。

## 为什么用 skill-hub？

管理 Agent 技能不应该浪费 Token。skill-hub 将技能的发现、安装和版本管理集中化，让你少花时间描述「这个技能是做什么的」，多花时间实际使用它。

- **单一事实来源** — 技能统一存放在 `~/.skills_repo/`，不再零散分布于聊天记录中
- **可视化发现** — 在 Web UI 中浏览技能元数据，无需通过 Agent 逐字阅读完整的 SKILL.md
- **一次同步，处处可用** — 一键安装到 `~/.claude/skills/` 和 `~/.agents/skills/`，避免反复进行「请帮我安装这个技能」的对话
- **版本感知** — 黄色圆点提示技能已过期，防止过时指令在后台静默消耗 Token
- **按需安装，避免全局膨胀** — 保持全局技能空间精简。项目专属技能安装到 `.agents/skills/`（私有），仅通用技能放入 `~/.agents/skills/`（全局）。作用域内无关技能越少，误匹配消耗的 Token 就越少

## 架构设计

### 数据流向

<p align="center"><img src="docs/assets/data-flow.svg" width="720" alt="skill-hub data flow"></p>

### 模块结构

```
src/skill_hub/
├── cli.py              # Click CLI 入口（web、version、self-update）
├── models.py           # SkillMetadata 数据类
├── version.py          # 版本解析与 GitHub 发行版检查
├── utils/
│   ├── __init__.py     # 路径工具（expand_path, derive_name）
│   └── yaml_parser.py  # SKILL.md YAML frontmatter 解析器
└── web/
    ├── app.py          # Flask 应用工厂
    ├── api.py          # REST API 路由
    ├── repos.py        # 仓库管理（克隆、扫描、安装）
    ├── state.py        # 已安装技能状态跟踪
    └── templates/
        └── index.html  # 单页 Web UI
```

## 安装

```bash
pip install skill-hub

# 或从 GitHub 安装
pip install git+https://github.com/wuerping/skill-hub.git

# 开发模式
pip install -e .
```

## 快速开始

```bash
# 启动 Web UI
skill-hub web

# 查看版本
skill-hub version

# 更新到最新版本
skill-hub self-update
```

浏览器自动打开 `http://127.0.0.1:7860`，你可以在界面上添加 GitHub 仓库或本地目录、浏览技能并安装到 `~/.claude/skills/` 和 `~/.agents/skills/`。

```bash
# 自定义端口
skill-hub web --port 8080

# 不自动打开浏览器
skill-hub web --no-open

# 检查更新但不安装
skill-hub version --check
```

## CLI 命令

| 命令 | 说明 |
|---------|-------------|
| `skill-hub web` | 启动 Web UI |
| `skill-hub version` | 显示当前版本 |
| `skill-hub version --check` | 检查是否有新版本可用 |
| `skill-hub self-update` | 通过 pip 升级 skill-hub |

## 工作原理

1. **添加 GitHub 仓库或本地目录** — 通过 UI 添加，远程仓库自动克隆到 `~/.skills_repo/repos/`，本地路径原地扫描
2. **自动发现技能** — 扫描仓库中的 `SKILL.md` 文件
3. **一键安装** — 将技能安装到 `~/.claude/skills/` 和 `~/.agents/skills/`
4. **同步状态** — 绿色圆点表示安装版本与源一致，黄色表示过期
5. **仓库同步** — 检测并拉取远端更新，每个仓库有同步状态指示（本地路径跳过克隆）

## 功能

- 技能按仓库分组展示（远程和本地）
- 每目录安装状态一目了然（绿色 = 与源一致，黄色 = 与源不同）
- 同时安装到 `~/.claude/skills` 和 `~/.agents/skills`
- 点击黄色圆点从源重新安装到对应目录
- 点击技能名称查看 `SKILL.md` frontmatter 元数据
- 添加/删除仓库，支持远端更新检测
- **异步克隆与进度条** — 远程仓库在后台克隆，实时显示进度条，失败可重试
- **本地目录支持** — 可将任意本地路径（如 `~/code/my-skills`）添加为技能源
- **推荐默认仓库** — 添加仓库表单中预填 `anthropics/skills` 作为快速入门建议
- **仓库诊断** — 🔍 按钮运行全面健康检查（git、网络、SKILL.md 文件、映射）

## SKILL.md 格式

```markdown
---
name: skill-name
description: 技能的简要描述
license: MIT
compatibility: cursor, claude, opencode
metadata:
  version: 1.0.0
  author: you@example.com
---

## 技能内容

你的技能说明在这里...
```

## 目录结构

```
~/.skills_repo/
├── repos.yaml             # 仓库列表配置
├── repos/                 # 克隆的 git 仓库
│   └── owner__repo/
│       └── ...
└── mappings/              # 技能位置映射（YAML）
    └── owner__repo.yaml

~/.claude/skills/          # 已安装技能（目标 A）
~/.agents/skills/          # 已安装技能（目标 B）
```

## 许可证

MIT
