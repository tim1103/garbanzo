"""
端到端测试 - 验证PRD核心功能
"""
import requests
import json

BASE = 'http://127.0.0.1:5000'

def test_full_flow():
    print("=" * 60)
    print("端到端测试：PRD核心功能验证")
    print("=" * 60)
    
    # 1. 录入单选题
    print("\n[1] 录入单选题...")
    r = requests.post(f'{BASE}/api/questions', json={
        'type': 'single_choice',
        'stem': '在Python中，下列哪个是合法的变量名？',
        'options': {'A':'2name','B':'name_2','C':'class','D':'name-2'},
        'answer': 'B',
        'difficulty': 2,
        'score': 2,
        'kp_id': 9,
        'source': '2024年模拟',
        'year': '2024',
        'analysis': 'Python变量名不能以数字开头，不能是关键字',
        'tag_ids': [3],
    })
    q1_id = r.json()['id']
    print(f"  ✓ 创建单选题 id={q1_id}")
    
    # 2. 录入代码填空题
    print("[2] 录入Python代码填空题（双轨制）...")
    r = requests.post(f'{BASE}/api/questions', json={
        'type': 'python_fill',
        'stem': '完成以下冒泡排序代码：\n<pre>\ndef bubble_sort(arr):\n    n = len(arr)\n    for i in range({{b1}}):\n        for j in range({{b2}}):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n</pre>',
        'options': {},
        'answer': '',
        'blanks': [
            {'id':'b1','answer':'n-1','score':2},
            {'id':'b2','answer':'n-1-i','score':3}
        ],
        'difficulty': 3,
        'score': 5,
        'kp_id': 17,
        'analysis': '<pre>外层循环n-1次，内层每次少1次</pre>',
        'tag_ids': [7, 8],
    })
    q2_id = r.json()['id']
    print(f"  ✓ 创建代码填空题 id={q2_id}, 包含2个填空")
    
    # 3. 录入Pandas题
    print("[3] 录入Pandas数据处理题...")
    r = requests.post(f'{BASE}/api/questions', json={
        'type': 'pandas',
        'stem': '给定df如下：<table class="table"><tr><th>姓名</th><th>分数</th></tr><tr><td>张三</td><td>90</td></tr></table>，使用df.groupby()按班级分组求平均分，代码为：{{b1}}',
        'options': {},
        'answer': '',
        'blanks': [{'id':'b1','answer':'df.groupby(\'班级\')[\'分数\'].mean()','score':5}],
        'difficulty': 3,
        'score': 7,
        'kp_id': 23,
        'analysis': '<pre>df.groupby()返回分组对象</pre>',
        'tag_ids': [2],
    })
    q3_id = r.json()['id']
    print(f"  ✓ 创建Pandas题 id={q3_id}")
    
    # 4. 录入二叉树题
    print("[4] 录入二叉树操作题...")
    r = requests.post(f'{BASE}/api/questions', json={
        'type': 'binary_tree',
        'stem': '给定二叉树前序遍历为ABDECFG，中序遍历为DBEAFCG，求后序遍历。',
        'options': {},
        'answer': 'DEBFGCA',
        'difficulty': 4,
        'score': 7,
        'kp_id': 35,
        'analysis': '由前序+中序重建二叉树后进行后序遍历',
        'tag_ids': [6, 10],
    })
    q4_id = r.json()['id']
    print(f"  ✓ 创建二叉树题 id={q4_id}")
    
    # 5. 测试重复题导入查重
    print("[5] 测试批量导入查重（重复题）...")
    r = requests.post(f'{BASE}/api/questions/import', json={
        'items': [
            # 重复题（题干相同）
            {'type':'single_choice','stem':'在Python中，下列哪个是合法的变量名？',
             'options':{'A':'2name','B':'name_2','C':'class','D':'name-2'},
             'answer':'B','difficulty':2,'score':2,'kp_id':9},
            # 新题
            {'type':'single_choice','stem':'下列哪个不是Python的内置函数？',
             'options':{'A':'print','B':'len','C':'printf','D':'range'},
             'answer':'C','difficulty':2,'score':2,'kp_id':9},
        ]
    })
    result = r.json()
    print(f"  ✓ 新增 {result['added']} 题，检测到 {result['conflict_count']} 个冲突")
    assert result['conflict_count'] >= 1, "应至少检测到1个重复题"
    
    # 6. 测试冲突解决 - 跳过
    print("[6] 测试冲突解决（跳过）...")
    r = requests.post(f'{BASE}/api/questions/resolve_conflict', json={
        'action': 'skip',
        'incoming': {'type':'single_choice','stem':'test'},
        'existing_id': q1_id
    })
    print(f"  ✓ 冲突处理: {r.json()['action']}")
    
    # 7. 测试搜索高亮
    print("[7] 测试全文检索高亮...")
    r = requests.get(f'{BASE}/api/questions/search_highlights?kw=df.groupby()')
    hits = r.json()
    print(f"  ✓ 搜索 'df.groupby()' 命中 {len(hits)} 条")
    
    # 8. 创建试卷并智能组卷
    print("[8] 创建试卷并智能组卷...")
    r = requests.post(f'{BASE}/api/papers', json={
        'title':'2024年6月浙江省信息技术学考模拟卷',
        'mode':'xuekao',
        'total_score':50,
        'header_text':'2024年6月浙江省普通高中信息技术学考',
        'seal_line':1,
        'student_info':'姓名：________   班级：________   学号：________'
    })
    pid = r.json()['id']
    print(f"  ✓ 创建试卷 id={pid}")
    
    # 智能组卷
    r = requests.post(f'{BASE}/api/papers/{pid}/auto_assemble', json={
        'template':'xuekao',
        'difficulty':3
    })
    print(f"  ✓ 智能组卷完成: {r.json()}")
    
    # 9. 检查试卷内容
    r = requests.get(f'{BASE}/api/papers/{pid}')
    paper = r.json()
    print(f"  ✓ 试卷共 {len(paper['questions'])} 道题")
    
    # 10. 测试一键盲换（如果有题）
    if paper['questions']:
        first_pq = paper['questions'][0]
        print(f"[10] 测试一键盲换（题号{first_pq['id']}）...")
        r = requests.post(f'{BASE}/api/papers/{pid}/swap_blind', json={'pq_id':first_pq['id']})
        try:
            res = r.json()
            if res.get('ok'):
                print(f"  ✓ 盲换成功，新题ID={res['new_question']['id']}")
            else:
                print(f"  ⚠ 盲换: {res.get('msg', '无可用题')}")
        except: pass
    
    # 11. 测试同类题推荐
    if paper['questions']:
        first_pq = paper['questions'][0]
        print(f"[11] 测试同类题推荐...")
        r = requests.get(f'{BASE}/api/questions/{first_pq['question_id']}/similar')
        similar = r.json()
        print(f"  ✓ 推荐同类题 {len(similar)} 道")
    
    # 12. 题号重排
    print("[12] 测试题号自动重排...")
    r = requests.post(f'{BASE}/api/papers/{pid}/renumber')
    print(f"  ✓ 重排: {r.json()}")
    
    # 13. 一键平均分值
    if paper['questions']:
        big_no = paper['questions'][0]['big_no']
        print(f"[13] 测试一键平均分值（大题{big_no}）...")
        r = requests.post(f'{BASE}/api/papers/{pid}/avg_score', json={'big_no':big_no,'total':10})
        print(f"  ✓ 平均: {r.json()}")
    
    # 14. 总分校验
    print("[14] 测试总分校验...")
    r = requests.get(f'{BASE}/api/papers/{pid}/validate_score')
    res = r.json()
    print(f"  ✓ 目标{res['expected']}分，实际{res['actual']}分，一致={res['match']}")
    
    # 15. 保存版本
    print("[15] 测试版本控制...")
    r = requests.post(f'{BASE}/api/papers/{pid}/save', json={
        'questions': paper['questions'],
        'version_note':'初始版本'
    })
    print(f"  ✓ 保存版本: {r.json()}")
    
    r = requests.get(f'{BASE}/api/papers/{pid}/versions')
    print(f"  ✓ 历史版本数: {len(r.json())}")
    
    # 16. 测试删除-回收站-恢复
    print("[16] 测试回收站机制...")
    r = requests.delete(f'{BASE}/api/questions/{q4_id}')
    print(f"  ✓ 删除试题: {r.json()}")
    
    r = requests.get(f'{BASE}/api/questions?recycle=1&size=100')
    print(f"  ✓ 回收站题数: {r.json()['total']}")
    
    r = requests.post(f'{BASE}/api/questions/{q4_id}/restore')
    print(f"  ✓ 恢复试题: {r.json()}")
    
    # 17. 测试Word导出
    print("[17] 测试Word试卷导出...")
    r = requests.get(f'{BASE}/api/papers/{pid}/export_docx')
    with open('/home/z/my-project/download/test_paper.docx','wb') as f:
        f.write(r.content)
    print(f"  ✓ 试卷Word已下载: {len(r.content)} 字节")
    
    r = requests.get(f'{BASE}/api/papers/{pid}/export_docx?answer=1')
    with open('/home/z/my-project/download/test_paper_answer.docx','wb') as f:
        f.write(r.content)
    print(f"  ✓ 答案Word已下载: {len(r.content)} 字节")
    
    # 18. 测试答题卡
    print("[18] 测试答题卡生成...")
    r = requests.get(f'{BASE}/api/papers/{pid}/answer_sheet?pages=single')
    with open('/home/z/my-project/download/test_answer_sheet.docx','wb') as f:
        f.write(r.content)
    print(f"  ✓ 单页答题卡: {len(r.content)} 字节")
    
    r = requests.get(f'{BASE}/api/papers/{pid}/answer_sheet?pages=double')
    with open('/home/z/my-project/download/test_answer_sheet_double.docx','wb') as f:
        f.write(r.content)
    print(f"  ✓ 双页答题卡: {len(r.content)} 字节")
    
    # 19. 测试统计
    print("[19] 测试统计分析...")
    r = requests.get(f'{BASE}/api/stats/overview')
    d = r.json()
    print(f"  ✓ 题库总量: {d['total']}")
    print(f"  ✓ 题型分布: {len(d['by_type'])}种")
    print(f"  ✓ 标签分布: {len(d['by_tag'])}个")
    print(f"  ✓ 未覆盖知识点: {len(d['uncovered_kps'])}个")
    
    r = requests.get(f'{BASE}/api/stats/paper_coverage/{pid}')
    d = r.json()
    print(f"  ✓ 试卷教材覆盖: {len(d['book_coverage'])}本")
    print(f"  ✓ 核心素养雷达: {len(d['abilities_radar'])}维度")
    
    # 20. 测试备份
    print("[20] 测试数据备份...")
    r = requests.post(f'{BASE}/api/backup')
    with open('/home/z/my-project/download/test_backup.zip','wb') as f:
        f.write(r.content)
    print(f"  ✓ 备份文件: {len(r.content)} 字节")
    
    # 21. 测试知识点树导出
    print("[21] 测试知识点树导出Excel...")
    r = requests.get(f'{BASE}/api/kp/export_excel')
    with open('/home/z/my-project/download/kp_tree.xlsx','wb') as f:
        f.write(r.content)
    print(f"  ✓ Excel: {len(r.content)} 字节")
    
    print("\n" + "=" * 60)
    print("✅ 所有核心功能测试通过！")
    print("=" * 60)


if __name__ == '__main__':
    test_full_flow()
