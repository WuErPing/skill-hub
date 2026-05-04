# 可扩展安装目录支持

**日期**: 2026-05-04
**作者**: skill-hub 设计
**状态**: 待实现

---

## 1. 背景

当前 skill-hub 硬编码了两个安装目标目录：
- `~/.claude/skills`
- `~/.agents/skills`

随着更多 AI 工具和自定义工作流的出现，用户需要支持任意数量的安装目录（如 `~/.cursor/skills`、`~/my-tools` 等）。但直接在 skill 列表中为每个目录添加一列会导致界面在目录较多时变得极度拥挤。

## 2. 目标

1. **支持用户自定义安装目录**：允许添加、删除任意本地目录作为安装目标
2. **保持界面紧凑**：即使目录数量很多，skill 列表行也不能过宽
3. **保留现有操作习惯**：一键安装/卸载仍在，单独目录操作路径最短
4. **状态一目了然**：不点击即可判断每个 skill 在每个目录的安装状态

## 3. 方案概述

采用**紧凑状态网格 + 目录管理器**方案：

- 用小型状态圆点（带首字母缩写）替代当前的"claude dot + 文字 + agents dot + 文字"
- 在设置菜单中新增"安装目录"配置面板
- Hover 圆点显示完整路径和单独操作按钮

## 4. 详细设计

### 4.1 目录管理（设置面板）

在设置菜单中新增 **"安装目录"** 区块：

```
安装目录
─────────────────────────
  ~/.claude/skills     [C]  [不可删除]
  ~/.agents/skills     [A]  [不可删除]
  ~/.cursor/skills     [Cr] [删除]
  ~/my-tools           [M]  [删除]
  
  [+ 添加目录]
```

**行为**：
- 显示完整路径和对应的缩写标识
- `~/.claude/skills` 和 `~/.agents/skills` 始终存在，不可删除
- 用户可添加任意本地目录（支持 `~` 展开）
- 可删除用户自定义目录
- 目录配置持久化到 `~/.skills_repo/config.json`

### 4.2 Skill 列表行布局

每行布局从：

```
[skill-name]  [● claude 🔗] [● agents]  [安装/卸载]
```

变为：

```
[skill-name]    [C] [A] [Cr] [M]    [安装] / [卸载]
```

**圆点规格**：
- 大小：`w-5 h-5`（当前 `w-2.5` 的 2 倍）
- 内容：目录首字母缩写，字体 `text-[10px] font-bold text-white`
- 颜色状态：
  - 🟢 **绿色背景** = 已安装且与源一致（md5 匹配）
  - 🟡 **黄色背景** = 已安装但与源不同步（可点击更新）
  - ⚪ **灰色背景** = 未安装
- **Symlink 标识**：圆点右下角叠加一个微型 🔗 链图标（`text-[8px] text-blue-400`）

### 4.3 Hover Tooltip

Hover 任意圆点时弹出 tooltip：

```
┌─────────────────────────────┐
│ ~/.cursor/skills            │
│ 状态: 已安装 (与源一致)      │
│ 方式: symlink               │
│                              │
│ [单独安装]  [单独卸载]       │
└─────────────────────────────┘
```

**行为**：
- Tooltip 延迟 200ms 出现，避免误触
- 点击 tooltip 内按钮执行对应操作
- Tooltip 在鼠标移出圆点或 tooltip 区域后 300ms 消失

### 4.4 首字母缩写算法

自动生成不冲突的缩写：

1. 取目录名的第一个字母（如 `claude` → `C`）
2. 若冲突，取前两个字母（如 `cursor` → `Cr`）
3. 若仍冲突，取前三个字母，以此类推
4. 若目录名完全相同（理论上不应发生，因为路径不同），在末尾加数字后缀

**示例**：

| 目录路径 | 缩写 |
|----------|------|
| `~/.claude/skills` | **C** |
| `~/.agents/skills` | **A** |
| `~/.cursor/skills` | **Cr** |
| `~/.custom/skills` | **Cu** |
| `~/my-tools` | **M** |
| `~/my-skills` | **My** |

### 4.5 总体操作按钮

保留右侧的 **"安装" / "卸载"** 按钮：
- **安装**：将 skill 安装到**所有**已配置目录
- **卸载**：将 skill 从**所有**已配置目录卸载
- 按钮文案不变，hover 时 tooltip 提示"安装到全部目录"

## 5. 数据模型改动

### 5.1 当前模型

```python
# state.py — 硬编码
CLAUDE_SKILLS = Path.home() / ".claude" / "skills"
AGENTS_SKILLS = Path.home() / ".agents" / "skills"

class SkillEntry:
    in_claude: bool
    in_agents: bool
    md5_claude: str
    md5_agents: str
    link_claude: bool
    link_agents: bool
```

### 5.2 新模型

```python
# 配置持久化
class InstallDir:
    path: str           # 绝对路径
    label: str          # 显示标签（如 "claude"）
    is_default: bool    # 是否不可删除

# SkillEntry 改为动态
class SkillEntry:
    # 动态安装目录状态：{dir_label: DirStatus}
    dir_status: dict[str, DirStatus]

class DirStatus:
    installed: bool
    md5: str
    is_symlink: bool
    matches_source: bool
```

### 5.3 API 响应格式

当前：
```json
{
  "name": "skill-name",
  "inClaude": true,
  "inAgents": false,
  "claudeMatchesSource": true,
  "agentsMatchesSource": false,
  "linkClaude": true,
  "linkAgents": false
}
```

新格式：
```json
{
  "name": "skill-name",
  "dirStatus": {
    "claude": {
      "installed": true,
      "matchesSource": true,
      "isSymlink": true
    },
    "agents": {
      "installed": false,
      "matchesSource": false,
      "isSymlink": false
    },
    "cursor": {
      "installed": true,
      "matchesSource": false,
      "isSymlink": false
    }
  }
}
```

**兼容性**：前端同步更新，不需要向后兼容（因为前后端同时发布）。

## 6. 配置存储

新增配置文件：`~/.skills_repo/config.json`

```json
{
  "installDirs": [
    {
      "path": "~/.claude/skills",
      "label": "claude",
      "isDefault": true
    },
    {
      "path": "~/.agents/skills",
      "label": "agents",
      "isDefault": true
    },
    {
      "path": "~/.cursor/skills",
      "label": "cursor",
      "isDefault": false
    }
  ]
}
```

**初始化**：
- 若文件不存在，自动生成包含两个默认目录的配置
- 读取时展开 `~` 为绝对路径

## 7. 界面截图示意

### 设置面板
```
┌─────────────────────────────────┐
│ ⚙️ 设置                         │
│                                 │
│ 仓库扫描间隔                      │
│ [30] 分钟                        │
│                                 │
│ ─────────────────────────────   │
│ 安装目录                          │
│                                 │
│  ~/.claude/skills     [C]       │
│  ~/.agents/skills     [A]       │
│  ~/.cursor/skills     [Cr]  [×] │
│                                 │
│  [+ 添加目录]                    │
│                                 │
│ ─────────────────────────────   │
│                                 │
│        [保存]                   │
└─────────────────────────────────┘
```

### Skill 列表
```
┌──────────────────────────────────────────┐
│ repo-name                                │
│                                          │
│  skill-a        [C] [A] [Cr]    [安装]   │
│  skill-b        [C] [A] [Cr]    [卸载]   │
│  skill-c        [●] [●] [●]     [安装]   │
│            ↑ 绿色  ↑ 黄色  ↑ 灰色         │
└──────────────────────────────────────────┘
```

## 8. 边界情况

1. **目录被外部删除**：启动时检查所有目录是否存在，不存在的标记为"缺失"，圆点变红色
2. **目录权限不足**：安装时捕获权限错误，显示具体哪个目录失败
3. **同名 skill 冲突**：保持现有行为（`conflict` 字段标记）
4. **空目录列表**：至少保留两个默认目录，不允许全部删除

## 9. 实现范围

**包含**：
- 后端：配置管理、动态目录扫描、API 接口更新
- 前端：设置面板、圆点组件、tooltip、列表渲染
- 初始化：配置文件自动迁移

**不包含**：
- 远程目录支持（仅本地路径）
- 目录优先级/覆盖逻辑
- 批量目录导入/导出

## 10. 验收标准

- [ ] 用户可以在设置中添加新的安装目录
- [ ] 添加后 skill 列表立即显示新目录的状态圆点
- [ ] 圆点首字母缩写自动生成且不冲突
- [ ] Hover 圆点显示完整路径和单独操作
- [ ] 一键安装/卸载仍作用于所有目录
- [ ] 默认两个目录不可删除
- [ ] 界面在 8 个目录下仍保持紧凑（不超出屏幕宽度）
