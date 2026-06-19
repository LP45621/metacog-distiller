# 🧠 Metacog Distiller — 个人知识图谱系统

> **原子化笔记 · 双向链接 · AI 认知伙伴**
>
> 一个遵循 **12 条宪法设计原则** 的个人知识管理系统，将 Markdown 原子笔记自动转化为交互式知识图谱，并配备 AI 认知伙伴辅助思考。

---

## 📋 目录

- [核心设计元语（12条宪法）](#-核心设计元语12条宪法)
- [快速开始](#-快速开始)
- [项目架构](#-项目架构)
- [核心组件](#-核心组件)
- [工作流程](#-工作流程)
- [12条宪法的实现](#-12条宪法的实现)
- [技术栈](#-技术栈)
- [开发指南](#-开发指南)

---

## ⚖️ 核心设计元语（12条宪法）

| # | 原则 | 实现方式 |
|---|------|----------|
| 1 | **原子化** — 一笔记一概念 | 每个 `notes/*.md` 文件只记录一个概念 |
| 2 | **双向链接** — 所有关联均双链 | `[[Wiki链接]]` 自动解析，backlinks 实时显示 |
| 3 | **渐进式形式化** — 结构由使用中生长 | 无需预定义 schema，从 [[链接]] 中自然生长出图谱 |
| 4 | **模糊与精确并存** — 标签与全文搜索共存 | 类型标签 + 全文搜索（`note_graph.py --search`） |
| 5 | **时间深度** — 记录知道时间 | 日志文件带时间戳，frontmatter 支持 `created/updated` |
| 6 | **发现惊喜** — 主动推荐旧笔记中的隐藏关联 | Cognitive Partner 共享邻居启发式发现潜在连接 |
| 7 | **语境保留** — 摘录永远带源链接 | 每个节点详情都有 "📄 打开笔记" 链接到源文件 |
| 8 | **知识复利** — 连接越多，自动关联越强 | 连接密度 → 写作建议触发（P11） |
| 9 | **可视化思考** — 局部图展开，非全局炫技 | 点击节点 → 局部展开关联子图 |
| 10 | **个人知识主权** — 本地明文，可迁移 | 全部 Markdown + JSON，无数据库依赖 |
| 11 | **输出自然涌现** — 密集区域自动触发写作建议 | Cognitive Partner 检测密集簇并推荐总结 |
| 12 | **AI 作为认知伙伴** — 只建议连接、提问，不做自动分类 | Cognitive Partner 模式仅提问和建议 |

---

## 🚀 快速开始

```bash
# 1. 构建所有图谱和可视化
cd metacog-system
python3 -X utf8 build_all.py

# 2. 启动交互式工作流（浏览器自动打开）
python3 -X utf8 metacog_workflow.py

# 3. 或者直接打开静态探索器
# 双击 knowledge-explorer.html

# 4. 搜索笔记
python3 -X utf8 note_graph.py --search 元认知

# 5. 启动笔记 HTTP 服务器（用于编辑器 + 笔记浏览）
python3 -X utf8 note_graph.py --serve
```

浏览器访问：
- **知识图谱浏览器** → `knowledge-explorer.html`（双击）
- **原子笔记编辑器** → `note-editor.html`（需要 HTTP 服务器）
- **元认知挖掘工作流** → `http://localhost:19800/`（运行 `metacog_workflow.py`）

---

## 🏗️ 项目架构

```
metacog-distiller/
│
├── notes/                          ← 📝 原子笔记（一概念一文件）
│   ├── 元认知蒸馏.md                 ← [[Wiki链接]] 自动解析
│   ├── CodeWhale.md
│   ├── RK3568+RTT嵌入式项目.md
│   └── ... (117+ 个原子笔记)
│
├── metacog-system/                 ← 🧠 后端引擎
│   ├── note_graph.py                ← 笔记 → 图谱管道（扫描 [[链接]]、解析反向链接）
│   ├── cognitive_partner.py         ← AI 认知伙伴（关联建议、反刍提醒、语境摘要）
│   ├── build_final_html.py          ← 原有图谱 HTML 生成器（已增强：搜索+反向链接）
│   ├── build_all.py                 ← 统一构建脚本
│   ├── metacog_workflow.py          ← 交互式工作流（挖掘模式 + 认知伙伴模式）
│   ├── init_atomic_notes.py         ← 从 JSON 图谱初始化原子笔记
│   ├── analyze.py                   ← 静态分析报告
│   ├── final_distill.py             ← 全量蒸馏管道
│   ├── clean_garbled.py             ← 乱码修复工具
│   ├── d3.v7.min.js                 ← D3.js 离线库
│   ├── note_graph.json              ← 自动生成的图谱数据
│   ├── metacog_graph.json           ← 元认知图谱
│   ├── knowledge_graph.json         ← 知识图谱
│   ├── learning_graph.json          ← 学习图谱
│   ├── knowledge_log.md             ← 知识日志（已去重）
│   └── observation_log.md           ← 元认知观测日志（已去重）
│
├── knowledge-explorer.html         ← 🌐 知识图谱浏览器（双击可用）
├── note-editor.html                 ← 📝 原子笔记编辑器（需 HTTP 服务）
├── metacognition-mapper.html        ← 🧠 元认知图谱（增强版）
├── knowledge-mapper.html            ← 📚 知识图谱（增强版）
├── learning-mapper.html             ← 📖 学习图谱（增强版）
│
├── data/                            ← 📦 原始数据
│   └── deepseek_export.json
│
├── reports/                         ← 📊 分析报告
│
└── d3.v7.min.js                     ← D3.js v7
```

---

## 🧩 核心组件

### 1. 原子笔记系统 (P1, P2, P10)

`notes/` 目录包含所有原子笔记，每个 `.md` 文件一个概念：

```markdown
---
title: 元认知蒸馏
type: concept
confidence: certain
depth: 2
---

# 元认知蒸馏

从AI对话日志中自动提取认知模式的技术。

参见 [[CodeWhale]]、[[D3.js力导向图]] 了解更多。
```

- 使用 `[[Wiki链接]]` 建立关联
- `note_graph.py` 自动扫描并解析双向链接
- 反向链接自动更新（无需手动维护）

### 2. 笔记 → 图谱管道 (P2, P9)

```bash
# 扫描所有笔记 → 构建图谱 JSON + 生成探索器 HTML
python3 -X utf8 note_graph.py

# 示例输出：
# 📊 Graph: 117 nodes, 136 edges → note_graph.json
# 🌐 Explorer → knowledge-explorer.html
```

- 解析 `[[Wiki链接]]` → 图谱节点 + 边
- 自动识别双向链接（76% 为双向链接）
- 生成 `knowledge-explorer.html` 交互式 D3.js 可视化

### 3. 知识图谱浏览器 (P9)

`knowledge-explorer.html` 提供：

- **左侧**：笔记列表 + 实时搜索过滤
- **中间**：D3.js 力导向图（双击节点局部展开）
- **右侧**：详情面板（摘要、向外链接、反向链接、笔记文件链接）
- **底部**：🔗 发现关联 / 🎲 随机笔记 / ↺ 重置视图

### 4. AI 认知伙伴 (P6, P7, P8, P11, P12)

`cognitive_partner.py` 实现了 AI 作为认知伙伴的五个核心功能：

| 功能 | 对应原则 | 描述 |
|------|----------|------|
| 🔗 连接建议 | P6 ✨ 发现惊喜 | 共享邻居启发式发现隐藏关联（如："A和B都连接了C，但它们之间没有直接链接"） |
| ⏰ 反刍提醒 | P6 ✨ 发现惊喜 | 提醒回访旧笔记（低连接度或高中心度节点） |
| 🌊 写作建议 | P11 🌊 输出自然涌现 | 在密集连接区域触发："这个节点有 N 条连接，可以考虑写一篇总结" |
| 📎 语境摘要 | P7 📎 语境保留 | BFS 展开邻居生成 Markdown 摘要，每条摘录带源文件链接 |
| 🤖 仅建议不分类 | P12 🤖 AI作为认知伙伴 | 从不自动分类/归入类别，只提问和连接建议 |

### 5. 统一构建管道

```bash
python3 -X utf8 build_all.py
# [1/4] Scanning atomic notes...
# [2/4] Building graph mappers...
# [3/4] Generating analysis report...
# [4/4] Verification...
# ✅ knowledge-explorer.html
# ✅ metacognition-mapper.html
# ✅ knowledge-mapper.html
# ✅ learning-mapper.html
```

---

## 🔄 工作流程

### 日常使用

```
写笔记 → 自动建立 [[链接]] → 运行 build_all.py → 查看图谱
   ↑                                              │
   └── Cognitive Partner 提醒回访 ←──────────────┘
```

### 笔记 → 图谱 → 发现 循环

```
1. 写笔记                       (原子化 P1)
   │
2. 使用 [[Wiki链接]] 建立关联    (双向链接 P2)
   │
3. note_graph.py 解析 → 图谱    (可视化思考 P9)
   │
4. 浏览器查看或双击打开          (个人主权 P10)
   │
5. Cognitive Partner 发现关联   (发现惊喜 P6)
   │
6. 触发新笔记或链接              (知识复利 P8)
   │
7. 密集区自动建议写作            (输出涌现 P11)
   │
   └──→ 回到 1
```

---

## 📊 12条宪法的实现

每条宪法的具体实现文件和验证方式：

### P1 原子化
- **文件**: `notes/*.md`
- **验证**: `ls notes/ | wc -l` → 117 个文件，每个一个概念

### P2 双向链接
- **文件**: `note_graph.py` + `cognitive_partner.py`
- **验证**: `note_graph.json` 中 76% 边为双向链接

### P3 渐进式形式化
- **文件**: 无需预定义 schema
- **验证**: 新笔记自动加入图谱，无需配置

### P4 模糊与精确
- **文件**: `note_graph.py --search` + 类型标签
- **验证**: `python3 note_graph.py --search 元认知` → 35 个匹配

### P5 时间深度
- **文件**: `knowledge_log.md`, `observation_log.md`, frontmatter
- **验证**: 日志文件全部带时间戳

### P6 发现惊喜
- **文件**: `cognitive_partner.py:suggest_connections()`
- **验证**: `GET /api/cognitive/suggest` → 3 条建议

### P7 语境保留
- **文件**: `cognitive_partner.py:summarize_cluster()`, HTML mappers
- **验证**: 每个节点详情有 "📄 打开笔记" 链接

### P8 知识复利
- **文件**: `cognitive_partner.py:get_writing_suggestion()`
- **验证**: 高连接度节点（如 RK3568 有 11 条边）→ 写作建议

### P9 可视化思考
- **文件**: `knowledge-explorer.html`, `*mapper.html`
- **验证**: 点击节点局部展开，非全局炫技

### P10 个人知识主权
- **文件**: 全部 Markdown + JSON
- **验证**: 无需数据库，纯文件可迁移

### P11 输出自然涌现
- **文件**: `cognitive_partner.py:get_writing_suggestion()`
- **验证**: 密集区域（≥8 连接）自动建议总结

### P12 AI作为认知伙伴
- **文件**: `cognitive_partner.py`, `metacog_workflow.py`
- **验证**: 模式切换：⛏️挖掘 → 🤖认知伙伴，只提问不分类

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **笔记格式** | Markdown + YAML frontmatter + `[[Wiki链接]]` |
| **图谱可视化** | D3.js v7 力导向图（离线 280KB） |
| **后端引擎** | Python 3 (no database, file-based) |
| **交互工作流** | Python http.server + HTML/CSS/JS |
| **搜索** | regex 全文搜索 (note_graph.py --search) |
| **AI 集成** | DeepSeek API (可选，用于元认知挖掘对话) |
| **认知伙伴** | 纯图算法（共享邻居 + 连接密度，无需 LLM） |

---

## 🧑‍💻 开发指南

### 添加新笔记

1. 在 `notes/` 下创建 `.md` 文件
2. 使用 `[[Wiki链接]]` 关联已有笔记
3. 运行 `python3 -X utf8 build_all.py` 重建图谱

### 添加新图谱类型

1. 修改 `note_graph.py` 中的节点类型颜色映射
2. 运行 `python3 -X utf8 note_graph.py` 重新生成

### 调试

```bash
# 验证图谱数据
python3 -X utf8 -c "import json; g=json.load(open('metacog-system/note_graph.json')); print(len(g['nodes']), 'nodes')"

# 检查 HTML 数据完整性
python3 -X utf8 -c "h=open('knowledge-explorer.html',encoding='utf-8').read(); print('Data OK:', 'var graphData =' in h)"

# 搜索笔记
python3 -X utf8 metacog-system/note_graph.py --search 关键词
```

---

## 📝 许可证

个人知识主权 (P10) —— 所有数据归你所有，MIT 许可证。

---

*Built with ❤️ by metacognitive distillation. 从对话中生长，在连接中涌现。*
