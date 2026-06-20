"""
主路由注册 - 所有API与页面路由
"""
import os
import json
import io
import re
import shutil
import uuid
import hashlib
from datetime import datetime, timedelta
from urllib.parse import quote

from flask import (Flask, request, jsonify, render_template, send_file,
                   redirect, url_for, flash, Response, abort)
from PIL import Image

from . import models
from .models import (db, query_all, query_one, execute, now_str, get_conn, DB_PATH)
from .word_export import export_paper_to_docx, export_answer_sheet
from . import paper_templates

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------- 题型常量 ----------
QUESTION_TYPES = {
    'single_choice': '单选题',
    'python_read': 'Python阅读题',
    'python_fill': 'Python代码填空题',
    'flowchart': '流程图分析题',
    'flask_fill': 'Flask代码填空题',
    'pandas': 'Pandas数据处理题',
    'binary_tree': '二叉树操作题',
    'linked_list': '链表操作题',
}


def register_routes(app):

    # ============== 页面路由 ==============
    @app.route('/')
    def index():
        return redirect(url_for('dashboard'))

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard/index.html', active='dashboard')

    @app.route('/questions')
    def questions_page():
        return render_template('questions/list.html', active='questions',
                               question_types=QUESTION_TYPES)

    @app.route('/questions/new')
    def question_new():
        return render_template('questions/edit.html', active='questions',
                               question_types=QUESTION_TYPES, qid=None)

    @app.route('/questions/<int:qid>/edit')
    def question_edit(qid):
        return render_template('questions/edit.html', active='questions',
                               question_types=QUESTION_TYPES, qid=qid)

    @app.route('/questions/recycle')
    def questions_recycle():
        return render_template('questions/recycle.html', active='questions')

    @app.route('/questions/import')
    def questions_import_page():
        return render_template('questions/import.html', active='questions')

    @app.route('/papers')
    def papers_page():
        return render_template('papers/list.html', active='papers')

    @app.route('/papers/new')
    def paper_new():
        return render_template('papers/edit.html', active='papers', pid=None)

    @app.route('/papers/<int:pid>/edit')
    def paper_edit(pid):
        return render_template('papers/edit.html', active='papers', pid=pid)

    @app.route('/papers/<int:pid>/preview')
    def paper_preview(pid):
        return render_template('papers/preview.html', active='papers', pid=pid)

    @app.route('/tags')
    def tags_page():
        return render_template('tags/tree.html', active='tags')

    @app.route('/backup')
    def backup_page():
        return render_template('dashboard/backup.html', active='backup')

    # ============== 知识点树 API ==============
    @app.route('/api/kp/tree')
    def kp_tree():
        rows = query_all("SELECT * FROM knowledge_points ORDER BY sort_order, id")
        # 构建树
        node_map = {r['id']: {**r, 'children': []} for r in rows}
        roots = []
        for r in rows:
            node = node_map[r['id']]
            if r['parent_id']:
                node_map[r['parent_id']]['children'].append(node)
            else:
                roots.append(node)
        return jsonify(roots)

    @app.route('/api/kp', methods=['POST'])
    def kp_add():
        d = request.json
        with db() as conn:
            cur = conn.execute(
                "INSERT INTO knowledge_points(parent_id,code,name,book,is_preset,sort_order,created_at) VALUES(?,?,?,?,0,?,?)",
                (d.get('parent_id'), d.get('code', ''), d['name'],
                 d.get('book', ''), d.get('sort_order', 0), now_str())
            )
            return jsonify({'id': cur.lastrowid, 'ok': True})

    @app.route('/api/kp/<int:kid>', methods=['PUT'])
    def kp_update(kid):
        d = request.json
        execute(
            "UPDATE knowledge_points SET name=?, code=?, book=?, sort_order=? WHERE id=?",
            (d.get('name'), d.get('code', ''), d.get('book', ''),
             d.get('sort_order', 0), kid)
        )
        return jsonify({'ok': True})

    @app.route('/api/kp/<int:kid>', methods=['DELETE'])
    def kp_delete(kid):
        execute("DELETE FROM knowledge_points WHERE id=?", (kid,))
        return jsonify({'ok': True})

    @app.route('/api/kp/export')
    def kp_export():
        """导出知识点树JSON"""
        rows = query_all("SELECT * FROM knowledge_points ORDER BY sort_order, id")
        return jsonify(rows)

    @app.route('/api/kp/import', methods=['POST'])
    def kp_import():
        """导入知识点树JSON - 增量合并：保留自定义，新增缺失项"""
        data = request.json.get('data', [])
        added = 0
        with db() as conn:
            # 获取已有code集合
            existing = {r['code'] for r in conn.execute("SELECT code FROM knowledge_points").fetchall() if r['code']}
            # 先清空系统预设再重灌（保留教师自定义 is_preset=0）
            conn.execute("DELETE FROM knowledge_points WHERE is_preset=1")
            from .knowledge_tree import SEED_TREE
            _import_tree_recursive(conn, data, None, 0, existing)
        return jsonify({'ok': True, 'added': added})

    @app.route('/api/kp/export_excel')
    def kp_export_excel():
        """导出Excel"""
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['编码', '名称', '所属教材', '父级编码', '是否预设'])
        rows = query_all("SELECT * FROM knowledge_points ORDER BY sort_order, id")
        id2code = {r['id']: r['code'] for r in rows}
        for r in rows:
            parent_code = id2code.get(r['parent_id'], '') if r['parent_id'] else ''
            ws.append([r['code'], r['name'], r['book'] or '', parent_code,
                      '是' if r['is_preset'] else '否'])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name='知识点树.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # ============== 标签 API ==============
    @app.route('/api/tags')
    def tags_list():
        rows = query_all("SELECT t.*, COUNT(qt.question_id) AS cnt FROM tags t "
                         "LEFT JOIN question_tags qt ON qt.tag_id=t.id "
                         "GROUP BY t.id ORDER BY t.name")
        return jsonify(rows)

    @app.route('/api/tags', methods=['POST'])
    def tag_add():
        d = request.json
        try:
            with db() as conn:
                cur = conn.execute("INSERT INTO tags(name,color,created_at) VALUES(?,?,?)",
                                   (d['name'], d.get('color', '#6c757d'), now_str()))
                return jsonify({'id': cur.lastrowid, 'ok': True})
        except Exception as e:
            return jsonify({'ok': False, 'msg': '标签名已存在'}), 400

    @app.route('/api/tags/<int:tid>', methods=['DELETE'])
    def tag_del(tid):
        execute("DELETE FROM tags WHERE id=?", (tid,))
        return jsonify({'ok': True})

    @app.route('/api/questions/batch_tags', methods=['POST'])
    def batch_tags():
        """批量打标签"""
        d = request.json
        qids = d.get('question_ids', [])
        tids = d.get('tag_ids', [])
        new_tags = d.get('new_tags', [])
        with db() as conn:
            # 新建标签
            for name in new_tags:
                cur = conn.execute("INSERT OR IGNORE INTO tags(name,color,created_at) VALUES(?,?,?)",
                                   (name, '#6c757d', now_str()))
                r = conn.execute("SELECT id FROM tags WHERE name=?", (name,)).fetchone()
                if r:
                    tids.append(r['id'])
            for qid in qids:
                for tid in tids:
                    conn.execute("INSERT OR IGNORE INTO question_tags(question_id,tag_id) VALUES(?,?)",
                                 (qid, tid))
        return jsonify({'ok': True})

    # ============== 试题 API ==============
    @app.route('/api/questions')
    def questions_list():
        """支持搜索/筛选/分页"""
        kw = request.args.get('kw', '').strip()
        qtype = request.args.get('type', '')
        kp_id = request.args.get('kp_id', '')
        tag_id = request.args.get('tag_id', '')
        difficulty = request.args.get('difficulty', '')
        only_deleted = request.args.get('recycle', '0') == '1'
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))

        where = ["q.is_deleted=?"]
        params = [1 if only_deleted else 0]
        if kw:
            where.append("(q.stem LIKE ? OR q.analysis LIKE ? OR q.answer LIKE ?)")
            params += [f'%{kw}%'] * 3
        if qtype:
            where.append("q.type=?")
            params.append(qtype)
        if kp_id:
            # 包含子节点
            kp_ids = _get_kp_subtree(int(kp_id))
            placeholders = ','.join('?' * len(kp_ids))
            where.append(f"q.kp_id IN ({placeholders})")
            params += kp_ids
        if tag_id:
            where.append("q.id IN (SELECT question_id FROM question_tags WHERE tag_id=?)")
            params.append(int(tag_id))
        if difficulty:
            where.append("q.difficulty=?")
            params.append(int(difficulty))

        where_clause = ' AND '.join(where)
        offset = (page - 1) * size
        sql = f"""SELECT q.*, kp.name AS kp_name
                  FROM questions q
                  LEFT JOIN knowledge_points kp ON kp.id=q.kp_id
                  WHERE {where_clause}
                  ORDER BY q.created_at DESC LIMIT ? OFFSET ?"""
        rows = query_all(sql, params + [size, offset])
        # 取标签
        for r in rows:
            r['tags'] = query_all(
                "SELECT t.* FROM tags t JOIN question_tags qt ON qt.tag_id=t.id WHERE qt.question_id=?",
                (r['id'],))
            # 摘要
            stem_text = re.sub(r'<[^>]+>', '', r['stem'] or '')
            r['summary'] = stem_text[:80]
        total = query_one(f"SELECT COUNT(*) AS c FROM questions q WHERE {where_clause}", params)['c']
        return jsonify({'list': rows, 'total': total, 'page': page, 'size': size})

    @app.route('/api/questions/<int:qid>')
    def question_get(qid):
        r = query_one("SELECT * FROM questions WHERE id=?", (qid,))
        if not r:
            abort(404)
        r['tags'] = query_all(
            "SELECT t.* FROM tags t JOIN question_tags qt ON qt.tag_id=t.id WHERE qt.question_id=?",
            (qid,))
        return jsonify(r)

    @app.route('/api/questions', methods=['POST'])
    def question_create():
        d = request.json
        now = now_str()
        with db() as conn:
            cur = conn.execute("""INSERT INTO questions
                (type,stem,options,answer,blanks,analysis,difficulty,score,kp_id,source,year,attachments,is_deleted,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,?,?)""",
                (d['type'], d.get('stem', ''), json.dumps(d.get('options', {}), ensure_ascii=False),
                 json.dumps(d.get('answer', ''), ensure_ascii=False) if not isinstance(d.get('answer'), str) else d.get('answer', ''),
                 json.dumps(d.get('blanks', []), ensure_ascii=False),
                 d.get('analysis', ''), d.get('difficulty', 3), d.get('score', 2),
                 d.get('kp_id'), d.get('source', ''), d.get('year', ''),
                 json.dumps(d.get('attachments', []), ensure_ascii=False),
                 now, now))
            qid = cur.lastrowid
            # 标签
            for tid in d.get('tag_ids', []):
                conn.execute("INSERT OR IGNORE INTO question_tags(question_id,tag_id) VALUES(?,?)",
                             (qid, tid))
        return jsonify({'id': qid, 'ok': True})

    @app.route('/api/questions/<int:qid>', methods=['PUT'])
    def question_update(qid):
        d = request.json
        now = now_str()
        execute("""UPDATE questions SET
            type=?,stem=?,options=?,answer=?,blanks=?,analysis=?,difficulty=?,score=?,
            kp_id=?,source=?,year=?,attachments=?,updated_at=? WHERE id=?""",
            (d['type'], d.get('stem', ''),
             json.dumps(d.get('options', {}), ensure_ascii=False),
             d.get('answer', '') if isinstance(d.get('answer'), str) else json.dumps(d.get('answer', ''), ensure_ascii=False),
             json.dumps(d.get('blanks', []), ensure_ascii=False),
             d.get('analysis', ''), d.get('difficulty', 3), d.get('score', 2),
             d.get('kp_id'), d.get('source', ''), d.get('year', ''),
             json.dumps(d.get('attachments', []), ensure_ascii=False),
             now, qid))
        # 标签更新
        with db() as conn:
            conn.execute("DELETE FROM question_tags WHERE question_id=?", (qid,))
            for tid in d.get('tag_ids', []):
                conn.execute("INSERT OR IGNORE INTO question_tags(question_id,tag_id) VALUES(?,?)",
                             (qid, tid))
        return jsonify({'ok': True})

    @app.route('/api/questions/<int:qid>', methods=['DELETE'])
    def question_delete(qid):
        """逻辑删除：进入回收站"""
        execute("UPDATE questions SET is_deleted=1, deleted_at=? WHERE id=?",
                (now_str(), qid))
        return jsonify({'ok': True})

    @app.route('/api/questions/<int:qid>/restore', methods=['POST'])
    def question_restore(qid):
        execute("UPDATE questions SET is_deleted=0, deleted_at=NULL WHERE id=?", (qid,))
        return jsonify({'ok': True})

    @app.route('/api/questions/<int:qid>/purge', methods=['DELETE'])
    def question_purge(qid):
        """彻底物理删除"""
        execute("DELETE FROM questions WHERE id=?", (qid,))
        execute("DELETE FROM question_tags WHERE question_id=?", (qid,))
        return jsonify({'ok': True})

    @app.route('/api/questions/recycle_cleanup', methods=['POST'])
    def recycle_cleanup():
        """清理过期回收站（30天）"""
        threshold = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        c, n = execute("DELETE FROM questions WHERE is_deleted=1 AND deleted_at < ?",
                       (threshold,))
        return jsonify({'ok': True, 'purged': n})

    @app.route('/api/questions/search_highlights')
    def questions_search_highlights():
        """全文检索 - 高亮代码片段"""
        kw = request.args.get('kw', '').strip()
        if not kw:
            return jsonify([])
        rows = query_all("""SELECT id, stem, type FROM questions
                            WHERE is_deleted=0 AND (stem LIKE ? OR analysis LIKE ?)
                            LIMIT 50""", (f'%{kw}%', f'%{kw}%'))
        results = []
        for r in rows:
            stem = r['stem'] or ''
            # 高亮所有匹配（包括代码片段中的）
            highlighted = re.sub(
                f'({re.escape(kw)})',
                r'<mark class="search-hit">\1</mark>',
                stem, flags=re.IGNORECASE
            )
            results.append({
                'id': r['id'],
                'type': r['type'],
                'snippet': highlighted[:500]
            })
        return jsonify(results)

    # ============== 批量导入与查重 ==============
    @app.route('/api/questions/import', methods=['POST'])
    def questions_import():
        """批量导入JSON，自动查重；返回冲突列表让前端逐条确认"""
        items = request.json.get('items', [])
        conflicts = []
        clean_items = []
        for idx, item in enumerate(items):
            # 查重：题干完全相同
            existing = query_one("SELECT id FROM questions WHERE stem=? AND is_deleted=0",
                                 (item.get('stem', ''),))
            if existing:
                conflicts.append({
                    'index': idx,
                    'incoming': item,
                    'existing_id': existing['id']
                })
            else:
                clean_items.append(item)

        # 直接导入无冲突的
        added_ids = []
        for item in clean_items:
            now = now_str()
            with db() as conn:
                cur = conn.execute("""INSERT INTO questions
                    (type,stem,options,answer,blanks,analysis,difficulty,score,kp_id,source,year,attachments,is_deleted,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,?,?)""",
                    (item['type'], item.get('stem', ''),
                     json.dumps(item.get('options', {}), ensure_ascii=False),
                     item.get('answer', ''),
                     json.dumps(item.get('blanks', []), ensure_ascii=False),
                     item.get('analysis', ''), item.get('difficulty', 3), item.get('score', 2),
                     item.get('kp_id'), item.get('source', ''), item.get('year', ''),
                     json.dumps(item.get('attachments', []), ensure_ascii=False),
                     now, now))
                qid = cur.lastrowid
                added_ids.append(qid)
                for tid in item.get('tag_ids', []):
                    conn.execute("INSERT OR IGNORE INTO question_tags(question_id,tag_id) VALUES(?,?)",
                                 (qid, tid))

        return jsonify({
            'ok': True,
            'added': len(added_ids),
            'added_ids': added_ids,
            'conflicts': conflicts,
            'conflict_count': len(conflicts)
        })

    @app.route('/api/questions/resolve_conflict', methods=['POST'])
    def resolve_conflict():
        """逐条处理冲突：overwrite / skip / keep_both"""
        d = request.json
        action = d['action']  # overwrite | skip | keep_both
        item = d['incoming']
        existing_id = d.get('existing_id')
        now = now_str()
        if action == 'skip':
            return jsonify({'ok': True, 'action': 'skip'})
        if action == 'overwrite':
            execute("""UPDATE questions SET
                type=?,options=?,answer=?,blanks=?,analysis=?,difficulty=?,score=?,
                kp_id=?,source=?,year=?,attachments=?,updated_at=? WHERE id=?""",
                (item['type'],
                 json.dumps(item.get('options', {}), ensure_ascii=False),
                 item.get('answer', ''),
                 json.dumps(item.get('blanks', []), ensure_ascii=False),
                 item.get('analysis', ''), item.get('difficulty', 3), item.get('score', 2),
                 item.get('kp_id'), item.get('source', ''), item.get('year', ''),
                 json.dumps(item.get('attachments', []), ensure_ascii=False),
                 now, existing_id))
            return jsonify({'ok': True, 'action': 'overwrite', 'id': existing_id})
        if action == 'keep_both':
            with db() as conn:
                cur = conn.execute("""INSERT INTO questions
                    (type,stem,options,answer,blanks,analysis,difficulty,score,kp_id,source,year,attachments,is_deleted,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,?,?)""",
                    (item['type'], item.get('stem', ''),
                     json.dumps(item.get('options', {}), ensure_ascii=False),
                     item.get('answer', ''),
                     json.dumps(item.get('blanks', []), ensure_ascii=False),
                     item.get('analysis', ''), item.get('difficulty', 3), item.get('score', 2),
                     item.get('kp_id'), item.get('source', ''), item.get('year', ''),
                     json.dumps(item.get('attachments', []), ensure_ascii=False),
                     now, now))
                new_id = cur.lastrowid
                for tid in item.get('tag_ids', []):
                    conn.execute("INSERT OR IGNORE INTO question_tags(question_id,tag_id) VALUES(?,?)",
                                 (new_id, tid))
            return jsonify({'ok': True, 'action': 'keep_both', 'id': new_id})
        return jsonify({'ok': False, 'msg': '未知操作'}), 400

    # ============== 图片上传 ==============
    @app.route('/api/upload_image', methods=['POST'])
    def upload_image():
        f = request.files.get('file')
        if not f:
            return jsonify({'ok': False, 'msg': '无文件'}), 400
        mode = request.form.get('mode', 'standard')  # standard | hd
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
            return jsonify({'ok': False, 'msg': '不支持的图片格式'}), 400
        img = Image.open(f.stream)
        if mode == 'standard':
            # 压缩至宽度800px，质量80%
            if img.width > 800:
                ratio = 800 / img.width
                img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=80, optimize=True)
            filename = f"{uuid.uuid4().hex}.jpg"
            with open(os.path.join(UPLOAD_DIR, filename), 'wb') as fo:
                fo.write(buf.getvalue())
            url = f"/static/uploads/{filename}"
            return jsonify({'ok': True, 'url': url, 'mode': 'standard'})
        else:
            filename = uuid.uuid4().hex + ext
            f.seek(0)
            f.save(os.path.join(UPLOAD_DIR, filename))
            url = f"/static/uploads/{filename}"
            return jsonify({'ok': True, 'url': url, 'mode': 'hd'})

    # ============== 试卷 API ==============
    @app.route('/api/papers')
    def papers_list():
        rows = query_all("SELECT * FROM papers ORDER BY created_at DESC")
        for r in rows:
            r['question_count'] = query_one(
                "SELECT COUNT(*) AS c FROM paper_questions WHERE paper_id=?", (r['id'],))['c']
        return jsonify(rows)

    @app.route('/api/papers/<int:pid>')
    def paper_get(pid):
        p = query_one("SELECT * FROM papers WHERE id=?", (pid,))
        if not p:
            abort(404)
        pqs = query_all("SELECT pq.*, q.type AS q_type, q.stem AS q_stem, q.options AS q_options, "
                        "q.answer AS q_answer, q.blanks AS q_blanks, q.analysis AS q_analysis, "
                        "q.kp_id AS q_kp_id, kp.name AS q_kp_name "
                        "FROM paper_questions pq "
                        "JOIN questions q ON q.id=pq.question_id "
                        "LEFT JOIN knowledge_points kp ON kp.id=q.kp_id "
                        "WHERE pq.paper_id=? ORDER BY pq.sort_order", (pid,))
        p['questions'] = pqs
        return jsonify(p)

    @app.route('/api/papers', methods=['POST'])
    def paper_create():
        d = request.json
        now = now_str()
        with db() as conn:
            cur = conn.execute("""INSERT INTO papers
                (title,mode,total_score,header_text,footer_text,seal_line,student_info,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (d['title'], d.get('mode', 'xuekao'), d.get('total_score', 50),
                 d.get('header_text', ''), d.get('footer_text', ''),
                 d.get('seal_line', 1), d.get('student_info', ''), now, now))
            pid = cur.lastrowid
        return jsonify({'id': pid, 'ok': True})

    @app.route('/api/papers/<int:pid>', methods=['PUT'])
    def paper_update(pid):
        d = request.json
        execute("""UPDATE papers SET
            title=?,mode=?,total_score=?,header_text=?,footer_text=?,seal_line=?,student_info=?,updated_at=?
            WHERE id=?""",
            (d['title'], d.get('mode', 'xuekao'), d.get('total_score', 50),
             d.get('header_text', ''), d.get('footer_text', ''),
             d.get('seal_line', 1), d.get('student_info', ''), now_str(), pid))
        return jsonify({'ok': True})

    @app.route('/api/papers/<int:pid>', methods=['DELETE'])
    def paper_delete(pid):
        execute("DELETE FROM papers WHERE id=?", (pid,))
        return jsonify({'ok': True})

    @app.route('/api/papers/<int:pid>/save', methods=['POST'])
    def paper_save(pid):
        """保存试卷题目结构 + 生成新版本"""
        d = request.json
        questions = d.get('questions', [])
        # 保存当前题目
        with db() as conn:
            conn.execute("DELETE FROM paper_questions WHERE paper_id=?", (pid,))
            for i, q in enumerate(questions):
                conn.execute("""INSERT INTO paper_questions
                    (paper_id,question_id,section,section_title,section_desc,big_no,small_no,custom_no,score,sort_order)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (pid, q['question_id'], q.get('section', ''), q.get('section_title', ''),
                     q.get('section_desc', ''), q.get('big_no', 0), q.get('small_no', 0),
                     q.get('custom_no', ''), q.get('score', 0), i))
            # 版本快照
            conn.execute("INSERT INTO paper_versions(paper_id,snapshot,version_note,created_at) VALUES(?,?,?,?)",
                         (pid, json.dumps(questions, ensure_ascii=False),
                          d.get('version_note', f'保存于 {now_str()}'), now_str()))
        return jsonify({'ok': True})

    @app.route('/api/papers/<int:pid>/versions')
    def paper_versions(pid):
        rows = query_all("SELECT id, version_note, created_at FROM paper_versions "
                         "WHERE paper_id=? ORDER BY id DESC", (pid,))
        return jsonify(rows)

    @app.route('/api/papers/<int:pid>/versions/<int:vid>')
    def paper_version_detail(pid, vid):
        r = query_one("SELECT * FROM paper_versions WHERE id=? AND paper_id=?", (vid, pid))
        if not r:
            abort(404)
        r['snapshot'] = json.loads(r['snapshot'])
        return jsonify(r)

    @app.route('/api/papers/<int:pid>/rollback/<int:vid>', methods=['POST'])
    def paper_rollback(pid, vid):
        r = query_one("SELECT snapshot FROM paper_versions WHERE id=? AND paper_id=?", (vid, pid))
        if not r:
            abort(404)
        questions = json.loads(r['snapshot'])
        with db() as conn:
            conn.execute("DELETE FROM paper_questions WHERE paper_id=?", (pid,))
            for i, q in enumerate(questions):
                conn.execute("""INSERT INTO paper_questions
                    (paper_id,question_id,section,section_title,section_desc,big_no,small_no,custom_no,score,sort_order)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (pid, q['question_id'], q.get('section', ''), q.get('section_title', ''),
                     q.get('section_desc', ''), q.get('big_no', 0), q.get('small_no', 0),
                     q.get('custom_no', ''), q.get('score', 0), i))
        return jsonify({'ok': True})

    @app.route('/api/papers/<int:pid>/renumber', methods=['POST'])
    def paper_renumber(pid):
        """题号自动重排"""
        pqs = query_all("SELECT * FROM paper_questions WHERE paper_id=? ORDER BY sort_order", (pid,))
        # 按section分组重排
        sections = {}
        for pq in pqs:
            sections.setdefault(pq['section'], []).append(pq)
        big_no = 0
        with db() as conn:
            for sec, items in sections.items():
                big_no += 1
                for i, pq in enumerate(items):
                    # 若同一大题下有多个小题
                    if len(items) > 1:
                        small_no = i + 1
                    else:
                        small_no = 0
                    # 重置custom_no（清空手动题号），让前端可见
                    conn.execute("UPDATE paper_questions SET big_no=?, small_no=? WHERE id=?",
                                 (big_no, small_no, pq['id']))
        return jsonify({'ok': True})

    # ============== 智能组卷 ==============
    @app.route('/api/papers/templates')
    def paper_templates_list():
        return jsonify(paper_templates.TEMPLATES)

    @app.route('/api/papers/<int:pid>/auto_assemble', methods=['POST'])
    def paper_auto_assemble(pid):
        """根据模板智能组卷"""
        d = request.json
        template = d.get('template', 'xuekao')
        spec = paper_templates.TEMPLATES.get(template)
        if not spec:
            return jsonify({'ok': False, 'msg': '未知模板'}), 400
        with db() as conn:
            conn.execute("DELETE FROM paper_questions WHERE paper_id=?", (pid,))
            sort_idx = 0
            big_no = 0
            # 单选
            single_spec = spec['single_choice']
            big_no += 1
            section_title = f"第{big_no}题（单选题，共{single_spec['count']}题，每题{single_spec['per_score']}分，共{single_spec['count'] * single_spec['per_score']}分）"
            candidates = _pick_questions(conn, 'single_choice', single_spec['count'], d.get('difficulty', 3), d.get('kp_id'))
            for i, q in enumerate(candidates):
                conn.execute("""INSERT INTO paper_questions
                    (paper_id,question_id,section,section_title,big_no,small_no,score,sort_order)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (pid, q['id'], 'single', section_title, big_no, i+1,
                     single_spec['per_score'], sort_idx))
                sort_idx += 1
            # 非选
            for ns in spec.get('non_choice', []):
                big_no += 1
                section_title = f"第{big_no}题（{QUESTION_TYPES.get(ns['type'],ns['type'])}，共{ns['count']}题，共{ns['count'] * ns['per_score']}分）"
                candidates = _pick_questions(conn, ns['type'], ns['count'], d.get('difficulty', 3), d.get('kp_id'))
                for i, q in enumerate(candidates):
                    conn.execute("""INSERT INTO paper_questions
                        (paper_id,question_id,section,section_title,big_no,small_no,score,sort_order)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (pid, q['id'], 'non_single', section_title, big_no, i+1,
                         ns['per_score'], sort_idx))
                    sort_idx += 1
        return jsonify({'ok': True})

    @app.route('/api/papers/<int:pid>/swap_blind', methods=['POST'])
    def swap_blind(pid):
        """一键盲换：按原标签抽题替换"""
        d = request.json
        pq_id = d['pq_id']
        pq = query_one("SELECT * FROM paper_questions WHERE id=?", (pq_id,))
        if not pq:
            abort(404)
        q = query_one("SELECT * FROM questions WHERE id=?", (pq['question_id'],))
        # 排除已在本卷中的题
        existing = query_all("SELECT question_id FROM paper_questions WHERE paper_id=?", (pid,))
        exclude_ids = [r['question_id'] for r in existing] + [q['id']]
        excl_placeholder = ','.join('?' * len(exclude_ids))
        # 同类型+同难度+同知识点
        cands = query_all(f"""SELECT * FROM questions WHERE is_deleted=0
            AND type=? AND difficulty=? AND id NOT IN ({excl_placeholder})
            ORDER BY RANDOM() LIMIT 1""",
            [q['type'], q['difficulty']] + exclude_ids)
        if not cands:
            # 放宽难度
            cands = query_all(f"""SELECT * FROM questions WHERE is_deleted=0
                AND type=? AND id NOT IN ({excl_placeholder})
                ORDER BY RANDOM() LIMIT 1""",
                [q['type']] + exclude_ids)
        if not cands:
            return jsonify({'ok': False, 'msg': '没有可替换的同类题'}), 400
        new_q = cands[0]
        execute("UPDATE paper_questions SET question_id=? WHERE id=?", (new_q['id'], pq_id))
        return jsonify({'ok': True, 'new_question': new_q})

    @app.route('/api/questions/<int:qid>/similar')
    def similar_questions(qid):
        """同类题推荐：同知识点/同难度/同类型"""
        q = query_one("SELECT * FROM questions WHERE id=?", (qid,))
        if not q:
            abort(404)
        cands = query_all("""SELECT * FROM questions WHERE is_deleted=0
            AND type=? AND id!=? ORDER BY
            CASE WHEN kp_id=? THEN 0 ELSE 1 END,
            CASE WHEN difficulty=? THEN 0 ELSE 1 END,
            RANDOM() LIMIT 10""",
            (q['type'], qid, q['kp_id'], q['difficulty']))
        return jsonify(cands)

    @app.route('/api/papers/<int:pid>/swap_with/<int:new_qid>', methods=['POST'])
    def swap_with(pid, new_qid):
        d = request.json
        pq_id = d['pq_id']
        execute("UPDATE paper_questions SET question_id=? WHERE id=?", (new_qid, pq_id))
        return jsonify({'ok': True})

    @app.route('/api/papers/<int:pid>/avg_score', methods=['POST'])
    def avg_score(pid):
        """一键平均小问分值"""
        d = request.json
        big_no = d['big_no']
        total = d['total']
        pqs = query_all("SELECT * FROM paper_questions WHERE paper_id=? AND big_no=?", (pid, big_no))
        if not pqs:
            return jsonify({'ok': False, 'msg': '无小题'}), 400
        avg = round(total / len(pqs), 2)
        with db() as conn:
            for pq in pqs:
                conn.execute("UPDATE paper_questions SET score=? WHERE id=?", (avg, pq['id']))
        return jsonify({'ok': True, 'avg': avg, 'scores': [avg] * len(pqs)})

    @app.route('/api/papers/<int:pid>/validate_score')
    def validate_score(pid):
        """校验总分一致性"""
        p = query_one("SELECT * FROM papers WHERE id=?", (pid,))
        if not p:
            abort(404)
        actual = query_one("SELECT COALESCE(SUM(score),0) AS s FROM paper_questions WHERE paper_id=?", (pid,))['s']
        return jsonify({
            'expected': p['total_score'],
            'actual': actual,
            'match': abs(actual - p['total_score']) < 0.01
        })

    # ============== 导出 ==============
    @app.route('/api/papers/<int:pid>/export_docx')
    def paper_export_docx(pid):
        p = query_one("SELECT * FROM papers WHERE id=?", (pid,))
        if not p:
            abort(404)
        pqs = query_all("SELECT pq.*, q.type AS q_type, q.stem AS q_stem, q.options AS q_options, "
                        "q.answer AS q_answer, q.blanks AS q_blanks, q.analysis AS q_analysis "
                        "FROM paper_questions pq JOIN questions q ON q.id=pq.question_id "
                        "WHERE pq.paper_id=? ORDER BY pq.sort_order", (pid,))
        buf = export_paper_to_docx(p, pqs, include_answer=bool(request.args.get('answer', '0') == '1'))
        fname = f"{p['title']}_{'答案' if request.args.get('answer') else '试卷'}.docx"
        return send_file(buf, as_attachment=True, download_name=fname,
                         mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    @app.route('/api/papers/<int:pid>/answer_sheet')
    def paper_answer_sheet(pid):
        p = query_one("SELECT * FROM papers WHERE id=?", (pid,))
        if not p:
            abort(404)
        pages = request.args.get('pages', 'single')  # single | double
        buf = export_answer_sheet(p, pages=pages)
        return send_file(buf, as_attachment=True,
                         download_name=f"{p['title']}_答题卡.docx",
                         mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    # ============== 统计 ==============
    @app.route('/api/stats/overview')
    def stats_overview():
        # 题库总量
        total = query_one("SELECT COUNT(*) AS c FROM questions WHERE is_deleted=0")['c']
        # 各题型分布
        by_type = query_all("""SELECT type, COUNT(*) AS cnt FROM questions
                              WHERE is_deleted=0 GROUP BY type""")
        # 各教材分布
        by_book = query_all("""SELECT kp.book, COUNT(*) AS cnt FROM questions q
                              LEFT JOIN knowledge_points kp ON kp.id=q.kp_id
                              WHERE q.is_deleted=0 GROUP BY kp.book""")
        # 各难度分布
        by_diff = query_all("""SELECT difficulty, COUNT(*) AS cnt FROM questions
                              WHERE is_deleted=0 GROUP BY difficulty ORDER BY difficulty""")
        # 各技术栈题量（基于标签）
        by_tag = query_all("""SELECT t.name, t.color, COUNT(qt.question_id) AS cnt
                             FROM tags t
                             LEFT JOIN question_tags qt ON qt.tag_id=t.id
                             LEFT JOIN questions q ON q.id=qt.question_id AND q.is_deleted=0
                             GROUP BY t.id ORDER BY cnt DESC""")
        # 知识点覆盖盲区
        all_kps = query_all("SELECT id, name, book FROM knowledge_points WHERE id NOT IN (SELECT DISTINCT kp_id FROM questions WHERE kp_id IS NOT NULL AND is_deleted=0) ORDER BY book, sort_order")
        # 试卷数
        paper_cnt = query_one("SELECT COUNT(*) AS c FROM papers")['c']
        return jsonify({
            'total': total,
            'paper_count': paper_cnt,
            'by_type': by_type,
            'by_book': by_book,
            'by_difficulty': by_diff,
            'by_tag': by_tag,
            'uncovered_kps': all_kps,
        })

    @app.route('/api/stats/paper_coverage/<int:pid>')
    def stats_paper_coverage(pid):
        """试卷对教材知识点的覆盖 + 核心素养雷达图数据"""
        pqs = query_all("""SELECT q.kp_id, kp.name, kp.book
                          FROM paper_questions pq
                          JOIN questions q ON q.id=pq.question_id
                          LEFT JOIN knowledge_points kp ON kp.id=q.kp_id
                          WHERE pq.paper_id=?""", (pid,))
        # 按教材统计覆盖率
        books = {'必修1': 0, '必修2': 0, '选择性必修1': 0, '选择性必修2': 0, '选择性必修3': 0}
        for r in pqs:
            if r['book'] in books:
                books[r['book']] += 1
        # 各书总知识点数
        book_total = {}
        for b in books:
            book_total[b] = query_one(
                "SELECT COUNT(*) AS c FROM knowledge_points WHERE book=?", (b,))['c']
        coverage = []
        for b in books:
            coverage.append({
                'book': b,
                'covered': books[b],
                'total_kp': book_total[b],
                'rate': (books[b] / book_total[b]) if book_total[b] else 0
            })
        # 核心素养雷达图（基于题型推断）
        # 计算思维、算法思维、数据意识、信息系统素养、创新设计
        abilities = {
            '计算思维': 0, '算法思维': 0, '数据意识': 0,
            '信息系统素养': 0, '创新设计': 0
        }
        type_ability_map = {
            'single_choice': ['计算思维', '数据意识'],
            'python_read': ['计算思维', '算法思维'],
            'python_fill': ['计算思维', '算法思维'],
            'flowchart': ['计算思维', '算法思维'],
            'flask_fill': ['信息系统素养', '计算思维'],
            'pandas': ['数据意识', '计算思维'],
            'binary_tree': ['算法思维', '计算思维'],
            'linked_list': ['算法思维', '计算思维'],
        }
        for r in pqs:
            q = query_one("SELECT type FROM questions WHERE id=?", (r['kp_id'] if False else 0,))
        # 重新查
        for pq in pqs:
            # 由于上面SQL没取type，这里再查一次
            pass
        # 实际查询
        pqs2 = query_all("""SELECT q.type FROM paper_questions pq
                            JOIN questions q ON q.id=pq.question_id
                            WHERE pq.paper_id=?""", (pid,))
        for r in pqs2:
            for ab in type_ability_map.get(r['type'], []):
                abilities[ab] += 1
        max_ab = max(abilities.values()) or 1
        radar = [{'name': k, 'value': round(v / max_ab * 100, 1)} for k, v in abilities.items()]
        return jsonify({
            'book_coverage': coverage,
            'abilities_radar': radar
        })

    # ============== 备份 ==============
    @app.route('/api/backup', methods=['POST'])
    def backup():
        """打包SQLite数据库与uploads目录为zip"""
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            db_path = os.path.join(BASE_DIR, 'data', 'exam.db')
            if os.path.exists(db_path):
                zf.write(db_path, 'exam.db')
            up_dir = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
            if os.path.exists(up_dir):
                for root, dirs, files in os.walk(up_dir):
                    for f in files:
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, BASE_DIR)
                        zf.write(full, arc)
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name=f'exam_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
                         mimetype='application/zip')

    # ============== 设置 ==============
    @app.route('/api/settings/<key>')
    def settings_get(key):
        r = query_one("SELECT v FROM settings WHERE k=?", (key,))
        return jsonify({'k': key, 'v': json.loads(r['v']) if r else None})

    @app.route('/api/settings/<key>', methods=['POST'])
    def settings_set(key):
        v = json.dumps(request.json.get('v'), ensure_ascii=False)
        with db() as conn:
            conn.execute("INSERT OR REPLACE INTO settings(k,v) VALUES(?,?)", (key, v))
        return jsonify({'ok': True})


def _get_kp_subtree(kp_id):
    """获取知识点及其所有子节点ID"""
    ids = [kp_id]
    queue = [kp_id]
    while queue:
        cur = queue.pop(0)
        rows = query_all("SELECT id FROM knowledge_points WHERE parent_id=?", (cur,))
        for r in rows:
            ids.append(r['id'])
            queue.append(r['id'])
    return ids


def _pick_questions(conn, qtype, count, difficulty=None, kp_id=None):
    """随机抽取题目"""
    sql = "SELECT * FROM questions WHERE is_deleted=0 AND type=?"
    params = [qtype]
    if difficulty:
        sql += " AND difficulty=?"
        params.append(difficulty)
    if kp_id:
        kp_ids = _get_kp_subtree(kp_id)
        if kp_ids:
            sql += f" AND kp_id IN ({','.join('?' * len(kp_ids))})"
            params += kp_ids
    sql += " ORDER BY RANDOM() LIMIT ?"
    params.append(count)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _import_tree_recursive(conn, nodes, parent_id, order, existing_codes):
    """递归导入知识点树 - 增量"""
    for i, node in enumerate(nodes):
        cur = conn.execute(
            "INSERT INTO knowledge_points(parent_id,code,name,book,is_preset,sort_order,created_at) VALUES(?,?,?,?,1,?,?)",
            (parent_id, node.get('code', ''), node['name'], node.get('book', ''),
             order + i, now_str()))
        new_id = cur.lastrowid
        if 'children' in node:
            _import_tree_recursive(conn, node['children'], new_id, 0, existing_codes)
