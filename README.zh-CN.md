# skill-hub

查看、安装、升级和管理 `~/.agents/skills` 目录中的技能。

## 安装

```bash
pip install -e .
```

## 使用方法

### 列出所有技能

```bash
skill-hub list
```

### 显示详细信息

```bash
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

## 技能生命周期管理

### 安装技能

从 GitHub 仓库、本地路径或 URL 安装技能：

```bash
# 从 GitHub 仓库安装
skill-hub install 用户名/仓库名/技能名称

# 使用自定义名称安装
skill-hub install 用户名/仓库名/技能名称 --as 我的技能

# 从本地路径安装
skill-hub install /path/to/skill

# 从 URL 安装
skill-hub install https://example.com/path/to/SKILL.md
```

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

## 目录结构

```
~/.agents/skills/
├── 技能名称-1/
│   └── SKILL.md
├── 技能名称-2/
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
| `skill-hub list` | 列出所有技能 |
| `skill-hub list --verbose` | 显示详细信息 |
| `skill-hub view <名称>` | 查看特定技能 |
| `skill-hub path` | 显示技能目录路径 |
| `skill-hub install <来源>` | 从 GitHub、本地路径或 URL 安装技能 |
| `skill-hub install <来源> --as <名称>` | 使用自定义名称安装 |
| `skill-hub upgrade <名称>` | 将技能升级为全局格式 |
| `skill-hub update` | 检查所有技能的更新 |
| `skill-hub update <名称>` | 检查特定技能的更新 |

## 许可证

MIT
