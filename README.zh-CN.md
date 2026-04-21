# skill-hub

基于 Web UI 的 GitHub 仓库和本地目录技能管理工具。

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
skill-hub web
```

浏览器自动打开 `http://127.0.0.1:7860`，你可以在界面上添加 GitHub 仓库或本地目录、浏览技能并安装到 `~/.claude/skills/` 和 `~/.agents/skills/`。

```bash
# 自定义端口
skill-hub web --port 8080

# 不自动打开浏览器
skill-hub web --no-open
```

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
- **本地目录支持** — 可将任意本地路径（如 `~/code/my-skills`）添加为技能源

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

## 架构设计

### 模块结构

```
src/skill_hub/
├── cli.py              # Click CLI 入口（仅 web 命令）
├── models.py           # SkillMetadata 数据类
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

### 数据流向

```
  GitHub / 本地路径                  ~/.skills_repo/               安装目标
                                     (本地缓存)                   (已安装)

       │                                  │                            │
       │  git clone（远程）               │                            │
       │  原地扫描（本地）               │                            │
       ▼                                  ▼                            ▼
 ┌───────────┐                  ┌─────────────────┐         ┌─────────────────┐
 │   源      │─────────────────►│   repos/        │         │ ~/.claude/      │
 │ （URL或   │                  │   (源码)        │         │   skills/       │
 │  路径）   │                  └─────────────────┘         └─────────────────┘
 └───────────┘                          │                            ▲
                                        │  扫描 SKILL.md             │
                                        ▼                            │
                               ┌─────────────────┐                   │
                               │   mappings/     │───────────────────┘
                               │   (技能索引)    │
                               └─────────────────┘
                                          │
                                          │  复制 / 安装
                                          ▼
                               ┌─────────────────┐
                               │ ~/.agents/      │
                               │   skills/       │
                               └─────────────────┘
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
