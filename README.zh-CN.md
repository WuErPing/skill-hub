# skill-hub

查看、安装、升级和管理 `~/.agents/skills` 目录中的技能。

## 安装

```bash
# 以可编辑模式安装（用于开发）
pip install -e .

# 或全局安装
pip install skill-hub

# 或从 GitHub 安装
pip install git+https://github.com/wuerping/skill-hub.git
```

## 多层技能目录架构

skill-hub 支持分层技能目录结构，包含**全局**（public）和**项目级**（project-level）技能目录：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              远程（REMOTE）                                     │
│                           GitHub                                               │
│  skill-hub install user/repo/skill-name --to public|private                    │
└───────────────────────────┬──────────────────────────────────┬───────────────┘
                            │                                  │
                            ▼                                  ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│          全局（PUBLIC）        │        │          全局（PUBLIC）        │
│   ~/.agents/skills/           │        │   ~/.claude/skills/           │
│   (全局共享)                   │◄──────►│   (全局 - 工具特定)            │
│                               │        │                               │
│   skill-hub list --public     │        │   skill-hub list --public     │
│   skill-hub install ...       │        │   skill-hub install ...       │
│   --to public                 │        │   --to public                 │
└───────────┬───────────────────┘        └───────────┬───────────────────┘
            │                                        │
            │     双向配置同步                        │
            │     (自动工具检测)                      │
            │                                        │
            ▼                                        ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│        项目级（PROJECT-LEVEL）│        │        项目级（PROJECT-LEVEL）│
│   .agents/skills/             │        │   .claude/skills/             │
│   (项目特定技能)               │        │   (项目特定技能)               │
│                               │        │                               │
│   skill-hub list --private    │        │   skill-hub list --private    │
│   skill-hub install ...       │        │   skill-hub install ...       │
│   --to private                │        │   --to private                │
│                               │        │                               │
│   skill-hub sync <skill>      │        │   skill-hub sync <skill>      │
│   --from public --to private  │        │   --from public --to private  │
└───────────┬───────────────────┘        └───────────┬───────────────────┘
            │                                        │
            │   优先级：项目级 > 全局                │
            │   (项目级技能覆盖全局技能)              │
            │                                        │
            ▼                                        ▼
         项目 A                               项目 B

# 列出所有技能并显示来源
$ skill-hub list --all

# 使用 dry-run 预览同步操作
$ skill-hub sync my-skill --from public --to private --dry-run
```

### 目录类型

**全局目录**（Global）：
- `~/.agents/skills/` - 代理级全局技能
- `~/.claude/skills/` - Claude 工具特定全局技能
- `~/.opencode/skills/` - Opencode 工具特定全局技能

**项目级目录**（Project-level）：
- `./.agents/skills/` - 代理级项目特定技能
- `./.claude/skills/` - Claude 工具特定项目级技能
- `./.*/skills/` - 其他工具特定项目级目录

### 优先级系统

当同名技能存在于多个目录时：

1. **项目级 > 全局** - 项目特定技能覆盖全局技能
2. **先发现优先** - 当存在多个项目级目录时，先发现的优先

这允许你：
- 在所有项目中共享全局技能
- 用项目特定自定义覆盖全局技能
- 将项目特定技能隔离到项目中

## 使用方法

### 列出所有技能

```bash
# 列出全局技能（默认）
skill-hub list

# 列出所有目录的技能
skill-hub list --all

# 仅列出项目级技能
skill-hub list --private

# 仅列出全局技能
skill-hub list --public

# 显示详细信息
skill-hub list --verbose
```

### 查看特定技能

```bash
skill-hub view <技能名称>
```

### 显示技能目录路径

```bash
skill-hub path
```

### 比较本地和全局技能

比较项目本地技能与全局技能：

```bash
# 完整比较表格
skill-hub compare

# 仅显示摘要（无详细表格）
skill-hub compare --summary

# 比较所有本地目录
skill-hub compare --all-locals
```

此命令比较项目本地技能（例如 `.opencode/skills`、`.agents/skills`）与全局技能（`~/.agents/skills`），并显示：

- **仅本地**: 仅在本地项目中的技能
- **仅全局**: 仅在全局目录中的技能
- **有可用更新**: 版本不同的技能
- **已最新**: 版本匹配的技能

## 技能生命周期管理

### 安装技能

从 GitHub 仓库、本地路径或 URL 安装技能：

```bash
# 安装到项目级目录（默认）
skill-hub install 用户名/仓库名/技能名称

# 安装到项目级目录（显式）
skill-hub install 用户名/仓库名/技能名称 --to private

# 安装到全局目录
skill-hub install 用户名/仓库名/技能名称 --to public

# 使用自定义名称安装
skill-hub install 用户名/仓库名/技能名称 --as 我的技能

# 从本地路径安装
skill-hub install /path/to/skill

# 从 URL 安装
skill-hub install https://example.com/path/to/SKILL.md
```

### 在目录间同步技能

显式在全局和项目级目录间同步技能（无自动双向同步）：

```bash
# 从全局同步到项目级
skill-hub sync 我的技能 --from public --to private

# 从项目级同步到全局
skill-hub sync 我的技能 --from private --to public

# Dry run - 预览操作而不实际执行
skill-hub sync 我的技能 --from public --to private --dry-run

# 强制覆盖现有技能
skill-hub sync 我的技能 --from public --to private --force
```

**重要**：同步命令需要显式用户操作。没有自动双向同步。

### 升级技能

将本地技能升级为全局格式，自动转换配置：

```bash
skill-hub upgrade 技能名称
```

此命令会将 `.claude` 配置转换为 `.agent` 格式，并在升级前创建备份。

### 检查更新

检查技能更新：

```bash
# 检查所有技能
skill-hub update

# 检查特定技能
skill-hub update 技能名称
```

### 版本管理

查看 skill-hub 版本和更新：

```bash
# 显示当前版本
skill-hub version

# 检查可用更新
skill-hub version --check
```

### 自我更新

更新 skill-hub 到最新版本：

```bash
skill-hub self-update
```

## 目录结构

### 全局（Global）结构

```
~/.agents/skills/
├── 技能名称-1/
│   └── SKILL.md
├── 技能名称-2/
│   └── SKILL.md
└── ...

~/.claude/skills/
├── 技能名称-1/
│   └── SKILL.md
└── ...
```

### 项目级（Project-level）结构

```
./.agents/skills/
├── 自定义技能-1/
│   └── SKILL.md
└── ...

./.claude/skills/
├── 自定义技能-2/
│   └── SKILL.md
└── ...
```

## SKILL.md 格式

```markdown
---
name: skill-name
description: 技能的简要描述
license: MIT (可选)
compatibility: cursor, claude, qoder (可选)
version: 1.0.0 (可选)
updateUrl: https://example.com/version.txt (可选)
---

## 技能内容

你的技能内容在这里...
```

### 版本跟踪

技能可以包含版本信息：

- `version`: 语义化版本（例如：`1.0.0`）
- `updateUrl`: 获取最新版本信息的 URL

示例：

```markdown
---
name: my-skill
description: 一个有用的技能
version: 1.2.3
updateUrl: https://raw.githubusercontent.com/user/repo/main/VERSION
---
```

## 命令参考

| 命令 | 描述 |
|------|------|
| `skill-hub list` | 列出全局技能（默认） |
| `skill-hub list --all` | 列出所有目录的技能 |
| `skill-hub list --private` | 仅列出项目级技能 |
| `skill-hub list --public` | 仅列出全局技能 |
| `skill-hub list --verbose` | 显示详细信息 |
| `skill-hub view <名称>` | 查看特定技能 |
| `skill-hub path` | 显示技能目录路径 |
| `skill-hub compare` | 比较本地和全局技能 |
| `skill-hub compare --summary` | 比较并仅显示摘要 |
| `skill-hub compare --all-locals` | 比较所有本地目录 |
| `skill-hub install <来源>` | 安装技能 |
| `skill-hub install <来源> --to public` | 安装到全局目录 |
| `skill-hub install <来源> --to private` | 安装到项目级目录 |
| `skill-hub install <来源> --as <名称>` | 使用自定义名称安装 |
| `skill-hub sync <名称> --from public --to private` | 从全局同步到项目级 |
| `skill-hub sync <名称> --from private --to public` | 从项目级同步到全局 |
| `skill-hub sync <名称> --from public --to private --dry-run` | Dry run 同步 |
| `skill-hub sync <名称> --from public --to private --force` | 强制同步（覆盖） |
| `skill-hub upgrade <名称>` | 将技能升级为全局格式 |
| `skill-hub update` | 检查所有技能的更新 |
| `skill-hub update <名称>` | 检查特定技能的更新 |
| `skill-hub version` | 显示当前版本 |
| `skill-hub version --check` | 检查可用更新 |
| `skill-hub self-update` | 更新 skill-hub 到最新版本 |

## 迁移指南

### 对于现有用户

如果你已经在使用 skill-hub，`~/.agents/skills/` 中的现有技能将继续完全按之前的方式工作。新的多层功能是附加的，向后兼容。

**开始使用项目级目录：**

1. 在项目中创建项目级技能目录：
   ```bash
   mkdir -p .agents/skills
   ```

2. 将技能安装到项目级目录：
   ```bash
   skill-hub install 用户名/仓库名/技能名称 --to private
   ```

3. 或将现有全局技能同步到项目级进行自定义：
   ```bash
   skill-hub sync 现有技能 --from public --to private
   ```

### 最佳实践

1. **全局技能**：用于可在所有项目中共享的通用技能
2. **项目级技能**：用于项目特定的自定义
3. **同步工作流**：在项目级进行更改，准备共享时同步到全局
4. **版本控制**：将 `.agents/skills/` 提交到项目仓库以便团队协作

## 示例

### 示例 1：用项目特定版本覆盖全局技能

```bash
# 安装全局技能
skill-hub install user/public-skill

# 同步到项目级进行自定义
skill-hub sync public-skill --from public --to private

# 编辑 .agents/skills/public-skill/SKILL.md

# 列表显示项目级版本优先
skill-hub list --all
```

### 示例 2：与团队共享技能

```bash
# 创建项目级技能目录
mkdir -p .agents/skills

# 安装团队特定技能到项目级
skill-hub install company/team-skill --to private

# 提交到仓库
git add .agents/skills/
git commit -m "添加团队特定技能"
```

### 示例 3：使用 dry-run 的工作流

```bash
# 检查将要同步的内容
skill-hub sync 我的技能 --from public --to private --dry-run

# 如果看起来正确，实际同步
skill-hub sync 我的技能 --from public --to private
```

## 许可证

MIT
