# skill-hub

查看、安装和管理 `~/.agents/skills` 目录中的技能。

## 安装

```bash
pip install skill-hub

# 或从 GitHub 安装
pip install git+https://github.com/wuerping/skill-hub.git

# 开发模式
pip install -e .
```

## 多层技能目录架构

skill-hub 支持**全局**（public）和**项目级**（private）技能目录：

```
                      远程来源
                  GitHub / URL / 本地路径
                  skill-hub install <source>
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌───────────────────────┐   ┌───────────────────────┐
│    全局（PUBLIC）      │   │   项目级（PRIVATE）    │
│                       │   │                       │
│  ~/.agents/skills/    │   │  .agents/skills/      │
│  ~/.claude/skills/    │   │  .claude/skills/      │
│                       │   │  .<tool>/skills/      │
└──────────┬────────────┘   └──────────┬────────────┘
           │                           │
           │   优先级：项目级 > 全局
           └──────────┬────────────────┘
                      ▼
                  技能发现

  # 在目录间同步
  $ skill-hub sync my-skill private public
  $ skill-hub sync my-skill public private
```

**优先级**：当同名技能同时存在于两个目录时，项目级（private）版本优先。

## 命令

### `list` — 列出技能

```bash
# 列出所有技能（全局 + 项目级），默认
skill-hub list

# 按范围过滤
skill-hub list --public
skill-hub list --private

# 详细输出
skill-hub list --verbose

# 显示项目级与全局的差异
skill-hub list --diff
```

### `view` — 查看技能

```bash
skill-hub view <技能名称>
```

### `install` — 安装技能

从本地路径、GitHub 仓库或 URL 安装技能。
默认安装到项目级（`./.agents/skills`）。

```bash
# 从本地路径安装（到项目级，默认）
skill-hub install /path/to/my-skill

# 安装到全局（~/.agents/skills）
skill-hub install /path/to/my-skill --to public

# 从 GitHub 安装
skill-hub install user/repo/skill-name

# 从 URL 安装
skill-hub install https://example.com/SKILL.md

# 使用自定义名称安装
skill-hub install /path/to/my-skill --as custom-name
```

### `sync` — 在目录间同步技能

FROM 和 TO 是位置参数：`public` 或 `private`。

```bash
# 项目级 → 全局
skill-hub sync my-skill private public

# 全局 → 项目级
skill-hub sync my-skill public private

# 也可以使用路径作为技能参数
skill-hub sync .agents/skills/my-skill private public

# 预览（不实际执行）
skill-hub sync my-skill private public --dry-run

# 强制覆盖
skill-hub sync my-skill private public --force
```

### `update` — 检查技能更新

```bash
# 检查 ~/.agents/skills 中的所有技能
skill-hub update

# 检查特定技能
skill-hub update my-skill
```

### `path` — 显示全局技能目录

```bash
skill-hub path
```

### `version` / `self-update`

```bash
skill-hub version
skill-hub version --check
skill-hub self-update
```

## 命令参考

| 命令 | 描述 |
|------|------|
| `skill-hub list` | 列出所有技能（全局 + 项目级） |
| `skill-hub list --public` | 仅列出全局技能 |
| `skill-hub list --private` | 仅列出项目级技能 |
| `skill-hub list --verbose` | 显示详细信息 |
| `skill-hub list --diff` | 显示项目级与全局的差异 |
| `skill-hub view <名称>` | 查看特定技能 |
| `skill-hub path` | 显示全局技能目录路径 |
| `skill-hub install <来源>` | 安装到项目级（默认） |
| `skill-hub install <来源> --to public` | 安装到全局 |
| `skill-hub install <来源> --to private` | 安装到项目级 |
| `skill-hub install <来源> --as <名称>` | 使用自定义名称安装 |
| `skill-hub sync <名称> private public` | 从项目级同步到全局 |
| `skill-hub sync <名称> public private` | 从全局同步到项目级 |
| `skill-hub sync <名称> <from> <to> --dry-run` | 预览同步 |
| `skill-hub sync <名称> <from> <to> --force` | 强制覆盖 |
| `skill-hub update` | 检查所有技能的更新 |
| `skill-hub update <名称>` | 检查特定技能的更新 |
| `skill-hub version` | 显示当前版本 |
| `skill-hub version --check` | 检查可用更新 |
| `skill-hub self-update` | 更新 skill-hub 到最新版本 |

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
~/.agents/skills/          # 全局（public）
├── skill-name-1/
│   └── SKILL.md
└── skill-name-2/
    └── SKILL.md

.agents/skills/            # 项目级（private）
├── custom-skill/
│   └── SKILL.md
└── ...
```

## 示例

### 用项目特定版本覆盖全局技能

```bash
# 将全局技能同步到项目级进行自定义
skill-hub sync public-skill public private

# 编辑 .agents/skills/public-skill/SKILL.md
# 项目级版本自动优先
skill-hub list
```

### 在项目间共享技能

```bash
# 先在项目中开发和测试
skill-hub install /path/to/new-skill

# 准备好后推广到全局
skill-hub sync new-skill private public
```

### 团队协作

```bash
# 将团队技能安装到项目目录
skill-hub install company/team-skill --to private

# 提交到仓库
git add .agents/skills/
git commit -m "添加团队技能"
```

## 许可证

MIT
