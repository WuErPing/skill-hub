# skill-hub

AI 编程助手（Cursor、Claude、Qoder、OpenCode）的统一技能管理系统。

[English](README.md) | 简体中文

## 概述

skill-hub 可以在多个平台上发现、同步和分发 AI 编程助手的技能。它在 `~/.skills/` 提供了一个中央仓库，确保所有助手都能访问相同的技能定义。

### 问题

AI 编程助手各自在独立的配置目录中维护自己的技能定义，导致：
- **重复**：相同的技能在不同的助手配置中存储多次
- **不一致**：当在一个位置更新技能时，其他位置的技能会失去同步
- **发现困难**：无法集中查看所有助手的可用技能
- **手动维护负担**：开发者必须手动在助手之间复制技能

### 解决方案

skill-hub 通过以下方式解决这些问题：
1. **发现**所有助手配置目录中的技能
2. **同步**它们到位于 `~/.skills/` 的中央仓库
3. **分发**更新后的技能到所有助手配置

## 功能特性

- 🔍 **多助手发现**：自动从 Cursor、Claude、Qoder 和 OpenCode 中查找技能
- 🔄 **双向同步**：从助手拉取技能到中央仓库，从中央仓库推送到助手
- ⚡ **增量更新**：仅同步变更的技能以提高性能
- 🔧 **可扩展**：插件架构，易于添加新的助手支持
- 🏥 **健康检查**：验证适配器配置和权限
- 📊 **丰富的 CLI**：精美的终端输出，包含表格和进度指示器
- 📦 **远程仓库**：从 GitHub 等平台拉取社区技能

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/skill-hub.git
cd skill-hub

# 开发模式安装
pip install -e .
```

### 从 PyPI 安装（即将推出）

```bash
pip install skill-hub
```

## 快速开始

### 1. 初始化配置

首次使用时，需要初始化配置：

```bash
# 交互式设置（推荐新手）
skill-hub init

# 快速设置（自动添加 Anthropic 技能仓库）
skill-hub init --with-anthropic

# 自定义仓库
skill-hub init --repo https://github.com/yourorg/team-skills
```

### 2. 拉取技能

从配置的远程仓库拉取技能：

```bash
skill-hub pull
```

### 3. 同步技能

在中央仓库和助手之间同步技能：

```bash
# 双向同步（先拉取后推送）
skill-hub sync

# 仅从助手拉取到中央仓库
skill-hub sync --pull

# 仅从中央仓库推送到助手
skill-hub sync --push
```

### 4. 列出技能

查看中央仓库中的所有技能：

```bash
skill-hub list
```

### 5. 检查助手健康状态

```bash
skill-hub agents --check
```

### 6. Web 界面

启动基于浏览器的 UI 来管理技能：

```bash
# 启动 Streamlit Web UI（默认）
skill-hub web

# 或使用 Flask 后端（旧版）
skill-hub web --backend flask
```

Web 界面提供：
- 📊 仪表板：快速操作和指标
- 🔄 同步控制（拉取/推送/双向）
- 📦 仓库管理（添加/列表/拉取）
- 🤖 助手健康检查
- ⚙️ 配置查看器
- 🔍 技能发现

## 新用户设置指南

当团队成员克隆本项目仓库后，需要设置他们的**本地用户配置**：

### 初始设置步骤

1. **安装项目：**
   ```bash
   git clone https://github.com/yourusername/skill-hub.git
   cd skill-hub
   pip install -e .
   ```

2. **初始化配置：**
   
   **方式 A：快速设置（推荐）**
   ```bash
   skill-hub init --with-anthropic
   ```
   
   **方式 B：交互式设置**
   ```bash
   skill-hub init
   # 按照提示添加仓库
   ```
   
   **方式 C：自定义仓库**
   ```bash
   skill-hub init --repo https://github.com/yourorg/team-skills
   ```

3. **拉取技能：**
   ```bash
   skill-hub pull
   ```

4. **分发到你的助手：**
   ```bash
   skill-hub sync
   ```

### 配置存储

**重要提示：** 配置存储在**每个用户**的 `~/.skills/.skill-hub/config.json`，而**不是**项目仓库中。这意味着：

- ✅ 每个用户配置自己的仓库
- ✅ 每个用户在 `~/.skills/` 管理自己的中央仓库
- ✅ 配置**不会**提交到 Git
- ✅ 团队成员可以通过文档共享技能仓库 URL

### 共享仓库配置

为了帮助团队成员，你可以在项目中记录推荐的仓库：

**方式 1：在项目 README 中添加一行命令**
```markdown
## 设置技能

安装后运行：
```bash
skill-hub init --with-anthropic --repo https://github.com/yourorg/team-skills
skill-hub pull
```
```

**方式 2：Shell 脚本** (`setup-skills.sh`)：
```bash
#!/bin/bash
set -e

echo "正在设置 skill-hub..."
skill-hub init --with-anthropic --repo https://github.com/yourorg/team-skills

echo "正在拉取技能..."
skill-hub pull

echo "正在分发到助手..."
skill-hub sync

echo "✓ 技能设置完成！"
```

### 私有仓库

对于私有 GitHub 仓库，设置环境变量：

```bash
export SKILL_HUB_GITHUB_TOKEN="ghp_your_token_here"
skill-hub pull
```

添加到你的 shell 配置文件（`~/.zshrc`、`~/.bashrc`）以在会话间保持。

## 支持的助手

| 助手 | 项目本地 | 全局 |
|-------|--------------|--------|
| **Cursor** | `.cursor/skills/` | `~/.cursor/skills/` |
| **Claude** | `.claude/skills/` | `~/.claude/skills/` |
| **Qoder** | `.qoder/skills/` | `~/.qoder/skills/` |
| **OpenCode** | `.opencode/skills/` | `~/.config/opencode/skills/` |

## 技能格式

技能必须在 `SKILL.md` 文件中定义，包含 YAML 前置元数据：

```markdown
---
name: git-release
description: 创建一致的发布和变更日志
license: MIT
compatibility: cursor, claude, qoder, opencode
---

## 我能做什么
- 从合并的 PR 中起草发布说明
- 建议版本号升级
- 提供可复制粘贴的 `gh release create` 命令

## 何时使用我
当你准备创建标签发布时使用此技能。
```

### 要求

- **name**：小写字母数字，单个连字符（1-64 字符）
- **description**：1-1024 字符
- **license**：可选的许可证标识符
- **compatibility**：可选的兼容性说明
- **metadata**：可选的键值对

## CLI 命令

### `skill-hub web`

启动 Web 界面，通过浏览器管理技能。

```bash
skill-hub web                           # 启动 Streamlit UI（默认，端口 8501）
skill-hub web --backend streamlit       # 显式指定 Streamlit 后端
skill-hub web --backend flask           # 使用 Flask 后端（端口 8000）
skill-hub web --host 0.0.0.0 --port 8080  # 自定义主机/端口
```

**功能特性：**
- **仪表板**：快速初始化、拉取和指标
- **同步**：双向、仅拉取或仅推送同步
- **中央仓库技能**：查看中央仓库中的所有技能
- **仓库**：添加/列表/移除远程仓库，拉取技能
- **助手**：列出适配器并运行健康检查
- **配置**：查看当前配置 JSON
- **发现**：从所有助手发现技能

**后端选项：**
- **Streamlit**（默认）：现代化、交互式 UI，支持自动重载
- **Flask**：轻量级 REST API + Vue.js 前端

### `skill-hub init`

初始化 skill-hub 配置并设置仓库。

```bash
skill-hub init                      # 交互式模式，带提示
skill-hub init --with-anthropic     # 自动添加 Anthropic 技能
skill-hub init --repo <url>         # 添加自定义仓库
skill-hub init --with-anthropic --repo https://github.com/org/repo  # 组合选项
```

**交互式模式示例：**
```
$ skill-hub init
正在初始化 skill-hub 配置...

快速设置：

添加 Anthropic 的社区技能仓库？ [Y/n]: y
  ✓ 已添加：https://github.com/anthropics/skills

添加自定义仓库？ [y/N]: y
  仓库 URL：https://github.com/myorg/skills
    ✓ 已添加
  再添加一个？ [y/N]: n

✓ 配置已保存到 ~/.skills/.skill-hub/config.json
  已配置 2 个仓库

下一步：
  1. 运行：skill-hub pull 获取技能
  2. 运行：skill-hub sync 分发到助手
```

### `skill-hub sync`

在中央仓库和助手之间同步技能。

```bash
skill-hub sync              # 双向同步（先拉取后推送）
skill-hub sync --pull       # 从助手拉取到中央仓库
skill-hub sync --push       # 从中央仓库推送到助手
skill-hub sync --verbose    # 显示详细日志
```

### `skill-hub discover`

从所有助手配置中发现技能。

```bash
skill-hub discover          # 以表格格式显示技能
skill-hub discover --json   # 导出为 JSON
```

### `skill-hub list`

列出中央仓库中的所有技能。

```bash
skill-hub list
```

### `skill-hub agents`

管理助手适配器。

```bash
skill-hub agents            # 列出所有适配器
skill-hub agents --check    # 运行健康检查
```

### `skill-hub repo`

管理远程技能仓库。

```bash
skill-hub repo add <url>           # 添加仓库
skill-hub repo add <url> --branch dev --path /skills  # 带选项
skill-hub repo list                # 列出已配置的仓库
skill-hub repo remove <url>        # 移除仓库
```

**示例：**
```bash
# 添加 Anthropic 的社区技能
skill-hub repo add https://github.com/anthropics/skills

# 添加特定分支
skill-hub repo add https://github.com/yourorg/skills --branch develop

# 添加子目录路径
skill-hub repo add https://github.com/example/repo --path /contrib/skills
```

### `skill-hub pull`

从远程仓库拉取技能。

```bash
skill-hub pull                      # 从所有启用的仓库拉取
skill-hub pull <url>                # 从特定仓库拉取
```

**功能说明：**
1. 克隆或更新仓库（使用 `--depth 1` 浅克隆）
2. 扫描 `SKILL.md` 文件
3. 导入技能到 `~/.skills/`
4. 跟踪提交哈希以实现增量更新
5. 保存元数据（同步次数、最后同步时间、导入的技能）

## 架构

```
skill-hub/
├── src/skill_hub/
│   ├── adapters/          # 助手特定的适配器
│   │   ├── cursor.py
│   │   ├── claude.py
│   │   ├── qoder.py
│   │   └── opencode.py
│   ├── discovery/         # 技能发现引擎
│   ├── sync/              # 同步引擎
│   ├── remote/            # 远程仓库管理
│   ├── utils/             # 工具（YAML 解析器、验证器）
│   ├── web/               # Web 界面
│   │   ├── app.py         # Flask 应用（REST API + Vue UI）
│   │   └── streamlit_app.py  # Streamlit 应用
│   ├── models.py          # 数据模型
│   └── cli.py             # 命令行界面
├── tests/                 # 单元和集成测试
└── openspec/              # OpenSpec 规范
```

## 开发

### 设置开发环境

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=skill_hub --cov-report=term-missing

# 格式化代码
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_utils.py

# 详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=skill_hub
```

## 配置

skill-hub 使用位于 `~/.skills/.skill-hub/config.json` 的配置文件：

```json
{
  "version": "1.0.0",
  "conflict_resolution": "newest",
  "agents": {
    "cursor": {
      "enabled": true,
      "global_path": null
    },
    "claude": {
      "enabled": true,
      "global_path": null
    }
  },
  "repositories": [
    {
      "url": "https://github.com/anthropics/skills",
      "enabled": true,
      "branch": "main",
      "path": "",
      "sync_schedule": null
    }
  ],
  "sync": {
    "incremental": true,
    "check_permissions": true,
    "create_directories": true,
    "remote_priority": false
  }
}
```

## 路线图

### 第一阶段（已完成）
- ✅ 多助手技能发现
- ✅ 双向同步
- ✅ 支持 Cursor、Claude、Qoder、OpenCode
- ✅ 基础冲突检测

### 第二阶段（已完成）
- ✅ 远程仓库支持（从 GitHub 等拉取）
- ✅ 配置管理系统
- ✅ 仓库元数据跟踪
- ✅ Web 界面（Streamlit + Flask）

### 第三阶段（未来）
- 🔲 Cron 定时同步
- 🔲 后台守护进程
- 🔲 系统服务集成（systemd/launchd）
- 🔲 文件监视自动同步
- 🔲 机器间云同步
- 🔲 技能验证和测试
- 🔲 高级冲突解决策略
- 🔲 技能市场/注册表

## 贡献

欢迎贡献！在提交 PR 之前，请阅读[贡献指南](CONTRIBUTING.md)。

### 添加新助手

要添加对新 AI 编程助手的支持：

1. 在 `src/skill_hub/adapters/` 创建新适配器：

```python
from skill_hub.adapters.base import AgentAdapter

class NewAgentAdapter(AgentAdapter):
    @property
    def name(self) -> str:
        return "newagent"

    @property
    def default_global_path(self) -> str:
        return "~/.newagent"

    @property
    def project_local_dirname(self) -> str:
        return ".newagent"
```

2. 在 `AdapterRegistry` 中注册
3. 添加测试
4. 更新文档

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)

## 致谢

- 使用 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 进行规范驱动开发
- 技能格式受 [OpenCode Skills](https://opencode.ai/docs/skills/) 启发
- CLI 使用 [Click](https://click.palletsprojects.com/) 和 [Rich](https://rich.readthedocs.io/) 构建

## 支持

- **问题反馈**：[GitHub Issues](https://github.com/yourusername/skill-hub/issues)
- **讨论**：[GitHub Discussions](https://github.com/yourusername/skill-hub/discussions)
- **文档**：[完整文档](https://skill-hub.readthedocs.io/)
