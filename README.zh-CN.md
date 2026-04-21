# skill-hub

基于 Web UI 的 GitHub 仓库技能管理工具。

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

浏览器自动打开 `http://127.0.0.1:7860`，你可以在界面上添加 GitHub 仓库、浏览技能并安装到 `~/.claude/skills/` 和 `~/.agents/skills/`。

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

## Web UI 功能

- 技能按仓库分组展示（远程 📁 和本地 📂）
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

### 模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                   skill-hub CLI (cli.py)                    │
└─────────────────────────────┬───────────────────────────────┘
                              │ click
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask App Factory (web/app.py)                 │
│                   ┌───────────────┐                         │
│                   │  HTML Template│                         │
│                   └───────────────┘                         │
└─────────────────────────────┬───────────────────────────────┘
                              │ api_bp
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                REST API Routes (web/api.py)                 │
│    /skills    /repos    /install    /sync    /meta          │
└──────┬────────────────────┬────────────────────┬────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Repos     │     │    State    │     │  YAML Parser    │
│(web/repos.  │     │(web/state.  │     │(utils/yaml_     │
│    py)      │     │    py)      │     │  parser.py)     │
└──────┬──────┘     └──────┬──────┘     └────────┬────────┘
       │                   │                     │
       │                   │                     ▼
       │                   │            ┌─────────────────┐
       │                   │            │     Models      │
       │                   │            │  (models.py)    │
       │                   │            └─────────────────┘
       │                   │
       │                   └──────────► Git + Filesystem
       │
       ▼
┌─────────────────┐
│   Path Utils    │
│(utils/path_     │
│  utils.py)      │
└─────────────────┘
```

### 数据流向

```
       GitHub                    ~/.skills_repo/               Targets
       (Remote)                  (Local Cache)                 (Installed)
                                    
         │                             │                            │
         │  git clone / pull           │                            │
         ▼                             ▼                            ▼
   ┌───────────┐              ┌─────────────────┐        ┌─────────────────┐
   │   Repo    │─────────────►│   repos/        │        │ ~/.claude/      │
   │   URL     │              │   (source code) │        │   skills/       │
   └───────────┘              └─────────────────┘        └─────────────────┘
         │                            │                           ▲
         │                            │  scan SKILL.md            │
         │                            ▼                           │
         │                   ┌─────────────────┐                  │
         └──────────────────►│   mappings/     │──────────────────┘
                             │   (skill index) │
                             └─────────────────┘
                                        │
                                        │  copy / install
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
