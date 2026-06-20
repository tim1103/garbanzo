"""
数据库模型 - SQLite + SQLAlchemy-style ORM（纯sqlite3实现，零额外依赖）
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'exam.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    book TEXT,            -- 必修1/必修2/选择性必修1/2/3
    is_preset INTEGER DEFAULT 1,  -- 1=系统预设 0=教师自定义
    sort_order INTEGER DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY(parent_id) REFERENCES knowledge_points(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#6c757d',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,                -- single_choice/python_read/python_fill/flowchart/flask_fill/pandas/binary_tree/linked_list
    stem TEXT NOT NULL,                -- 题干（HTML/Markdown混合）
    options TEXT,                      -- 单选选项JSON: {"A":"...","B":"..."}
    answer TEXT,                       -- 单选答案(A/B/C/D) 或代码填空答案JSON
    blanks TEXT,                       -- 填空信息JSON: [{"id":"b1","answer":"...","score":2}]
    analysis TEXT,                     -- 解析（富文本，支持图片/代码块/LaTeX）
    difficulty INTEGER DEFAULT 3,      -- 1-5
    score REAL DEFAULT 2,              -- 默认分值
    kp_id INTEGER,
    source TEXT,                       -- 来源
    year TEXT,                         -- 年份
    attachments TEXT,                  -- 附件URL列表JSON
    is_deleted INTEGER DEFAULT 0,
    deleted_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY(kp_id) REFERENCES knowledge_points(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS question_tags (
    question_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY(question_id, tag_id),
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    mode TEXT,                          -- xuekao/xuan kao
    total_score REAL DEFAULT 50,
    header_text TEXT,                   -- 页眉
    footer_text TEXT,                   -- 页脚
    seal_line INTEGER DEFAULT 1,        -- 是否有密封线
    student_info TEXT,                  -- 考生信息区文本
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS paper_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    section TEXT,                       -- 单选/非选
    section_title TEXT,                 -- 大题标题
    section_desc TEXT,                  -- 大题说明
    big_no INTEGER,                     -- 大题号
    small_no INTEGER,                   -- 小题号(0表示无小题)
    custom_no TEXT,                     -- 教师手动修改的题号(优先级最高)
    score REAL DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS paper_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    snapshot TEXT NOT NULL,             -- paper_questions快照JSON
    version_note TEXT,
    created_at TEXT,
    FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    k TEXT PRIMARY KEY,
    v TEXT
);
"""


def init_db():
    with db() as conn:
        conn.executescript(SCHEMA)
        # 内置浙江省知识点树
        from .knowledge_tree import SEED_TREE
        cur = conn.execute("SELECT COUNT(*) FROM knowledge_points")
        if cur.fetchone()[0] == 0:
            _seed_knowledge_tree(conn, SEED_TREE)
        # 内置题型预设标签
        cur = conn.execute("SELECT COUNT(*) FROM tags")
        if cur.fetchone()[0] == 0:
            for t in [('Python基础', '#28a745'), ('Pandas', '#fd7e14'),
                      ('Flask', '#dc3545'), ('算法', '#6f42c1'),
                      ('硬件网络', '#17a2b8'), ('二叉树', '#e83e8c'),
                      ('链表', '#20c997'), ('排序', '#ffc107'),
                      ('二分', '#6c757d'), ('递归', '#007bff')]:
                conn.execute("INSERT INTO tags(name,color,created_at) VALUES(?,?,?)",
                             (t[0], t[1], now_str()))


def _seed_knowledge_tree(conn, tree, parent_id=None, order=0):
    """递归插入知识点树"""
    for i, node in enumerate(tree):
        cur = conn.execute(
            "INSERT INTO knowledge_points(parent_id,code,name,book,is_preset,sort_order,created_at) VALUES(?,?,?,?,?,?,?)",
            (parent_id, node.get('code', ''), node['name'], node.get('book', ''), 1, order + i, now_str())
        )
        new_id = cur.lastrowid
        if 'children' in node:
            _seed_knowledge_tree(conn, node['children'], new_id, 0)


# ============== CRUD 通用辅助 ==============
def query_all(sql, args=()):
    with db() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def query_one(sql, args=()):
    with db() as conn:
        r = conn.execute(sql, args).fetchone()
        return dict(r) if r else None


def execute(sql, args=()):
    with db() as conn:
        cur = conn.execute(sql, args)
        return cur.lastrowid, cur.rowcount
