# 个人题库与试卷管理系统 V3.0

> 浙江省高中信息技术学科专属版 · Python Flask + SQLite + B/S架构

## 项目简介

为浙江省高中信息技术教师打造的轻量化、私有化、学科专属出题备课工具。彻底解决传统Word排版中Python代码缩进易乱、Pandas表格难画、代码填空排版困难、二叉树/链表手动绘制低效等核心痛点。

## 核心特性

- **学科专属**：内置浙江省信息技术学科知识点树（学考2本必修 + 选考3本选择性必修，共92个知识点）
- **轻量私有**：单用户本地/局域网访问，SQLite本地存储，无云端依赖
- **专注备课**：去除组织权限、多人协作、在线考试、考后分析等非核心功能
- **极致排版**：Word导出采用Consolas字体、Tab+下划线填空对齐、防跨页、无水印

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Python Flask 3.x |
| 数据库 | SQLite |
| 数据库ORM | 原生sqlite3 |
| Word导出 | python-docx |
| Excel导出 | openpyxl |
| 图片处理 | Pillow |
| 前端 | Bootstrap 5 + ECharts |
| 代码编辑器 | Monaco Editor |
| 公式渲染 | MathJax |
| 流程图 | Mermaid |

## 安装与启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动系统
python run.py

# 3. 浏览器访问
# 本地: http://127.0.0.1:5000
# 局域网: http://<本机IP>:5000
```

## 目录结构

```
my-project/
├── run.py                    # 启动入口
├── requirements.txt
├── data/
│   └── exam.db               # SQLite数据库（运行后生成）
├── app/
│   ├── __init__.py           # Flask应用工厂
│   ├── models.py             # SQLite数据模型
│   ├── knowledge_tree.py     # 浙江省知识点树种子数据
│   ├── routes_main.py        # 全部API与页面路由
│   ├── paper_templates.py    # 试卷模板（学考/选考）
│   ├── word_export.py        # Word导出（PRD排版终极方案）
│   ├── data/                  # （备份兼容路径）
│   ├── static/
│   │   ├── css/app.css
│   │   ├── js/app.js
│   │   └── uploads/          # 图片附件存储
│   └── templates/
│       ├── base.html
│       ├── dashboard/        # 工作台与备份
│       ├── questions/        # 题库（列表/录入/导入/回收站）
│       ├── papers/           # 试卷（列表/编辑/预览）
│       └── tags/             # 知识点树与标签
└── scripts/
    ├── start_daemon.sh       # 守护进程启动脚本
    ├── seed_data.py          # 种子数据
    └── e2e_test.py           # 端到端测试
```

## PRD功能对照表

### 一、平台基础管理

| PRD要求 | 实现位置 |
|---------|---------|
| B/S轻量架构 | Flask + 浏览器访问 |
| 后端Python Flask + SQLite | `app/__init__.py`, `models.py` |
| 知识点树增量更新（保留自定义） | `routes_main.py` `/api/kp/import` |
| Excel/JSON导入导出知识点 | `/api/kp/export_excel`, `/api/kp/export`, `/api/kp/import` |
| 题型预设（8种） | `routes_main.py` `QUESTION_TYPES` |

### 二、试题录入与编辑

| PRD要求 | 实现位置 |
|---------|---------|
| Monaco编辑器双轨制（选中设为填空 + 集中管理面板） | `questions/edit.html` |
| Pandas表格粘贴校验（合并单元格/多层级表头报错） | `checkTablePaste()` |
| 图片高清/标准模式（800px/80%质量自动压缩） | `/api/upload_image` |
| 解析区富文本（图片/代码块/LaTeX） | `analysisEditor` + MathJax |
| 批量导入查重弹窗（覆盖/跳过/保留两份） | `questions/import.html` + `/api/questions/resolve_conflict` |
| 全文检索高亮代码片段 | `/api/questions/search_highlights` |
| 批量打标签 | `/api/questions/batch_tags` |
| 回收站30天自动物理删除 | `is_deleted + deleted_at` + `/api/questions/recycle_cleanup` |

### 三、试卷管理与归档

| PRD要求 | 实现位置 |
|---------|---------|
| 学考卷模板（50分：单选10+非选2） | `paper_templates.py` `xuekao` |
| 选考卷模板（50分：单选12+非选3） | `paper_templates.py` `xuankao` |
| 一键盲换（按原标签抽题） | `/api/papers/<pid>/swap_blind` |
| 同类题推荐面板（同知识点/难度） | `/api/questions/<qid>/similar` |
| 非选题"一键平均"分值 | `/api/papers/<pid>/avg_score` |
| 总分一致性校验 | `/api/papers/<pid>/validate_score` |
| 题号自动重排 + 支持手动修改 | `/api/papers/<pid>/renumber` + `custom_no`字段 |
| 三种预览视图（适应宽度/100%/双页并排） | `papers/preview.html` `setView()` |
| 版本控制与回滚 | `/api/papers/<pid>/versions` + `/rollback` |

### 四、Word导出与打印（排版终极方案）

| PRD要求 | 实现位置 |
|---------|---------|
| 代码字体Consolas | `word_export.py` `_add_code_block` |
| 填空下划线Tab+前导符（绝对平齐） | `word_export.py` `_add_code_block` (w:leader="underscore") |
| 代码跨页直接截断 | `_keep_with_next(p, False)` |
| 自定义密封线/页眉/页脚/考生信息区/大题说明/计分框 | `_add_seal_line`, `_add_score_box` 等 |
| 无水印 | 未添加任何水印逻辑 |
| 单页/双页答题卡 | `/api/papers/<pid>/answer_sheet?pages=single|double` |

### 五、个人统计分析

| PRD要求 | 实现位置 |
|---------|---------|
| 各技术栈题量分布 | `/api/stats/overview` `by_tag` |
| 知识点覆盖盲区 | `/api/stats/overview` `uncovered_kps` |
| 试卷教材覆盖率 | `/api/stats/paper_coverage/<pid>` `book_coverage` |
| 核心素养雷达图 | `/api/stats/paper_coverage/<pid>` `abilities_radar` |

### 六、非功能需求

| PRD要求 | 实现位置 |
|---------|---------|
| 组卷接口 ≤ 5秒 | SQLite索引 + RANDOM()抽样 |
| Word导出 ≤ 15秒 | python-docx流式生成 |
| Chrome 90+/Edge 90+ | 使用标准ES6 + CDN库 |
| LocalStorage草稿自动保存（每分钟） | `app.js` `DraftAutoSave` 类 |
| 崩溃恢复弹窗 | `_checkRestore()` + 恢复模态框 |
| 快捷键Tab跳转填空 | Monaco `addCommand(Tab)` |
| 快捷键Esc关闭弹窗 | `setupGlobalShortcuts()` |
| 快捷键Ctrl+Enter保存 | `data-shortcut="save"` |
| SQLite备份指引 | `/backup` 页面 + `/api/backup` |

## 验收标准对照

### 7.1 核心功能验收

| 验收项 | 状态 |
|--------|------|
| 代码填空双轨制（编辑器选中生成 + 面板集中管理） | ✅ 已实现 |
| 解析区插入图片/代码块/LaTeX公式 | ✅ 已实现 |
| 批量导入重复题暂停弹窗逐条确认 | ✅ 已实现 |
| 换题支持一键盲换和同类推荐 | ✅ 已实现 |
| 非选择题支持总分控制下的小问分值微调 | ✅ 已实现 |
| 题号增删后自动重排，且允许手动修改 | ✅ 已实现 |

### 7.2 体验与稳定性验收

| 验收项 | 状态 |
|--------|------|
| 录题界面LocalStorage防丢失，重开提示恢复草稿 | ✅ 已实现 |
| 代码填空编辑区Tab键跳转下一填空位 | ✅ 已实现 |
| 删除试题进入回收站，30天倒计时自动物理清除 | ✅ 已实现 |

## 快速测试

```bash
# 1. 启动系统
python run.py

# 2. 运行端到端测试（覆盖21项核心功能）
python scripts/e2e_test.py

# 3. 录入种子数据
python scripts/seed_data.py
```

## 数据备份

详见 `/backup` 页面。简言之：
1. 关闭系统
2. 拷贝 `data/exam.db` 和 `app/static/uploads/` 两份内容
3. 存入U盘或网盘任意位置

或调用 `/api/backup` 接口生成zip备份包。
