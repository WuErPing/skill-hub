# skill-hub

AI 编程助手（Antigravity、Claude、Codex、Copilot、Cursor、Gemini CLI、OpenCode、Qoder、Windsurf）的统一技能管理系统。

[English](README.md) | 简体中文

> 🎉 **v0.2.0 新功能**：支持 `.agents/skills/` 标准目录 - 用于项目特定技能的统一、跨助手位置。[了解更多](#共享技能目录agentsskills)

![skill-hub Web 界面](docs/images/dashboard.png)

*现代化 Web 界面显示仪表板，包含 `.agents/skills/` 标准支持、快速操作和入门指南。*

## 概述

skill-hub 可以在多个平台上发现、同步和分发 AI 编程助手的技能。它在 `~/.agents/skills/` 提供了一个中央仓库，确保所有助手都能访问相同的技能定义。

### 问题

AI 编程助手各自在独立的配置目录中维护自己的技能定义，导致：
- **重复**：相同的技能在不同的助手配置中存储多次
- **不一致**：当在一个位置更新技能时，其他位置的技能会失去同步
- **发现困难**：无法集中查看所有助手的可用技能
- **手动维护负担**：开发者必须手动在助手之间复制技能

### 解决方案

skill-hub 通过以下方式解决这些问题：
1. **发现**所有助手配置目录中的技能
2. **同步**它们到位于 `~/.agents/skills/` 的中央仓库
3. **分发**更新后的技能到所有助手配置

## 功能特性

- 🔍 **多助手发现**：自动从 9+ AI 编程助手中查找技能
- 🔄 **双向同步**：从助手拉取技能到中央仓库，从中央仓库推送到助手
- 🎯 **共享技能标准**：支持 `.agents/skills/` 目录用于跨助手的项目技能
- ⚡ **增量更新**：仅同步变更的技能以提高性能
- 🔧 **可扩展**：插件架构，易于添加新的助手支持
- 🏥 **健康检查**：验证适配器配置、权限和共享技能检测
- 📊 **丰富的 CLI**：精美的终端输出，包含表格和进度指示器
- 🌐 **Web 界面**：现代化 FastAPI + HTMX + Tailwind CSS Web UI，实时更新
- 📦 **远程仓库**：从官方和社区仓库拉取技能
- 👁️ **技能预览**：在浏览器中查看技能详情，支持 Markdown 渲染

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

启动基于浏览器的 UI 来管理技能（会自动在默认浏览器中打开）：

```bash
# 启动 FastAPI Web UI（默认）- 自动打开浏览器
skill-hub web

# 选择不同的后端
skill-hub web --backend streamlit
skill-hub web --backend flask

# 启动但不打开浏览器
skill-hub web --no-browser
```

#### Web 界面截图

**仪表板 - 快速操作和入门指南**

![仪表板](docs/images/dashboard.png)

*仪表板显示 54 个中央仓库技能、仓库数量、快速操作以及包含 `.agents/skills/` 标准的入门指南。*

**AI 技能查找器 - 语义搜索界面**

![AI 技能查找器](docs/images/ai-finder.png)

*AI 驱动的技能查找器，支持自然语言搜索。输入类似"git workflow"的查询来查找相关技能，带有匹配分数和推理说明。*

**技能预览 - Markdown 渲染与双语翻译**

![技能预览](docs/images/skill-preview.png)

*技能预览页面，支持 Markdown 渲染和按需 AI 翻译为中文。英中双语对照视图，方便比较。*

**AI/LLM 配置 - 统一提供商设置**

![AI/LLM 配置](docs/images/config-ai.png)

*配置本地 Ollama 或云端 OpenAI 兼容 API。在提供商之间切换、测试连接并管理 API 设置。*

**助手健康检查 - 适配器状态**

![助手健康检查](docs/images/agents-health.png)

*所有 9 个助手适配器的健康检查结果，显示状态、全局路径和 `.agents/skills/` 共享目录检测。*

**技能中心 - 中央仓库视图**

![技能中心](docs/images/skills-hub.png)

*中央仓库显示所有 54 个可用技能及其描述和兼容性。点击任意技能名称即可预览。*

**同步操作 - 三种模式**

![同步操作](docs/images/sync.png)

*在中央仓库和助手之间同步技能，提供三种模式：双向、仅拉取或仅推送同步。*

**仓库管理 - 远程来源**

![仓库管理](docs/images/repositories.png)

*管理远程技能仓库。添加官方来源（Anthropic、Vercel、Cloudflare、Supabase）或自定义仓库。*

Web 界面提供：
- 📊 仪表板：快速操作、健康检查和指标，包含 `.agents/skills/` 标准信息
- 🔄 同步控制（拉取/推送/双向）实时显示结果
- 📦 仓库管理（添加/列表/拉取）从 GitHub 拉取技能
- 🤖 助手健康检查，支持共享技能检测
- ⚙️ 配置查看器
- 🔍 技能发现，包括共享目录
- 👁️ 技能预览，支持 Markdown 渲染

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

**重要提示：** 配置存储在**每个用户**的 `~/.agents/skills/.skill-hub/config.json`，而**不是**项目仓库中。这意味着：

- ✅ 每个用户配置自己的仓库
- ✅ 每个用户在 `~/.agents/skills/` 管理自己的中央仓库
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

| 助手 | 项目本地 | 全局 | 状态 |
|-------|--------------|--------|--------|
| **Antigravity** | `.agent/skills/` | `~/.antigravity/skills/` | ✅ v0.2.0 |
| **Claude** | `.claude/skills/` | `~/.claude/skills/` | ✅ v0.1.0 |
| **Codex** | `.codex/skills/` | `~/.codex/skills/` | ✅ v0.2.0 |
| **GitHub Copilot** | `.github/skills/` | `~/.copilot/skills/` | ✅ v0.2.0 |
| **Cursor** | `.cursor/skills/` | `~/.cursor/skills/` | ✅ v0.1.0 |
| **Gemini CLI** | `.gemini/skills/` | `~/.gemini/skills/` | ✅ v0.2.0 |
| **OpenCode** | `.opencode/skills/` | `~/.config/opencode/skills/` | ✅ v0.1.0 |
| **Qoder** | `.qoder/skills/` | `~/.qoder/skills/` | ✅ v0.1.0 |
| **Windsurf** | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` | ✅ v0.2.0 |

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

启动 Web 界面，通过浏览器管理技能。浏览器会自动打开。

```bash
skill-hub web                           # 启动 FastAPI UI（默认，端口 8501，自动打开浏览器）
skill-hub web --backend fastapi         # 显式指定 FastAPI 后端（HTMX + Tailwind）
skill-hub web --backend streamlit       # 使用 Streamlit 后端
skill-hub web --backend flask           # 使用 Flask 后端（Vue.js + Element Plus）
skill-hub web --host 0.0.0.0 --port 8080  # 自定义主机/端口
skill-hub web --no-browser              # 启动但不打开浏览器
```

**功能特性：**
- **仪表板**：快速初始化、拉取和指标
- **同步**：双向、仅拉取或仅推送同步
- **中央仓库技能**：查看中央仓库中的所有技能及描述
- **AI 技能查找器**：AI 驱动的语义搜索，查找相关技能
- **技能预览**：点击任意技能名称查看完整内容，支持 Markdown 渲染
- **仓库**：添加/列表/移除远程仓库，拉取技能
- **助手**：列出适配器并运行健康检查
- **配置**：查看当前配置 JSON
- **发现**：从所有助手发现技能

**后端选项：**
- **FastAPI**（默认）：现代化、快速异步后端，使用 HTMX + Tailwind CSS，类 SPA 体验
- **Streamlit**：交互式 Python 原生 UI，支持自动重载
- **Flask**：轻量级 REST API + Vue.js + Element Plus 前端

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

✓ 配置已保存到 ~/.agents/skills/.skill-hub/config.json
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
3. 导入技能到 `~/.agents/skills/`
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

skill-hub 使用位于 `~/.agents/skills/.skill-hub/config.json` 的配置文件：

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

### 第一阶段（已完成 - v0.1.0）
- ✅ 多助手技能发现
- ✅ 双向同步
- ✅ 支持 4 个 AI 助手（Cursor、Claude、Qoder、OpenCode）
- ✅ 基础冲突检测

### 第二阶段（已完成 - v0.2.0）
- ✅ 扩展生态系统支持（新增 5 个助手：Antigravity、Codex、Copilot、Gemini CLI、Windsurf）
- ✅ 共享技能目录标准（`.agents/skills/`）
- ✅ 统一中央仓库位置（`~/.agents/skills/`）
- ✅ 远程仓库支持（从 GitHub 等拉取）
- ✅ 配置管理系统
- ✅ 仓库元数据跟踪
- ✅ Web 界面（FastAPI + HTMX + Tailwind CSS、Streamlit、Flask）
- ✅ Web 命令自动打开浏览器
- ✅ 官方仓库集成（Anthropic、Vercel Labs、Cloudflare、Supabase、Qoder Community）
- ✅ 国际化支持（英文和中文）

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
