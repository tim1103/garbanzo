"""
种子数据 - 录入多道试题供智能组卷使用
"""
import requests
import json

BASE = 'http://127.0.0.1:5000'

QUESTIONS = [
    # 单选题 × 12（满足学考和选考模板）
    {'type':'single_choice','stem':'在Python中，表达式 3 ** 2 的结果是？',
     'options':{'A':'6','B':'9','C':'8','D':'12'},'answer':'B','difficulty':1,'score':2,'kp_id':9,
     'analysis':'** 是幂运算符','tag_ids':[3]},
    {'type':'single_choice','stem':'下列哪个是Python列表的合法操作？',
     'options':{'A':'list.add(1)','B':'list.append(1)','C':'list.push(1)','D':'list.insert_end(1)'},'answer':'B','difficulty':1,'score':2,'kp_id':12,
     'tag_ids':[3]},
    {'type':'single_choice','stem':'在Pandas中，读取CSV文件的函数是？',
     'options':{'A':'pd.read_csv()','B':'pd.load_csv()','C':'pd.open_csv()','D':'pd.csv_read()'},'answer':'A','difficulty':2,'score':2,'kp_id':21,
     'tag_ids':[2]},
    {'type':'single_choice','stem':'HTTP协议默认使用的端口号是？',
     'options':{'A':'21','B':'22','C':'80','D':'443'},'answer':'C','difficulty':2,'score':2,'kp_id':31,
     'tag_ids':[5]},
    {'type':'single_choice','stem':'下列哪个不是二叉树的遍历方式？',
     'options':{'A':'前序遍历','B':'中序遍历','C':'后序遍历','D':'随机遍历'},'answer':'D','difficulty':2,'score':2,'kp_id':35,
     'tag_ids':[6]},
    {'type':'single_choice','stem':'Flask框架中，路由装饰器是？',
     'options':{'A':'@app.route','B':'@app.url','C':'@app.path','D':'@app.view'},'answer':'A','difficulty':2,'score':2,'kp_id':27,
     'tag_ids':[1]},
    {'type':'single_choice','stem':'下列哪个时间复杂度最优？',
     'options':{'A':'O(n²)','B':'O(n log n)','C':'O(n)','D':'O(log n)'},'answer':'D','difficulty':3,'score':2,'kp_id':16,
     'tag_ids':[4]},
    {'type':'single_choice','stem':'链表相比数组的优势是？',
     'options':{'A':'随机访问快','B':'插入删除快','C':'占用内存少','D':'排序快'},'answer':'B','difficulty':3,'score':2,'kp_id':34,
     'tag_ids':[10]},
    {'type':'single_choice','stem':'SQL中用于查询数据的关键字是？',
     'options':{'A':'GET','B':'FETCH','C':'SELECT','D':'QUERY'},'answer':'C','difficulty':1,'score':2,'kp_id':41,
     'tag_ids':[5]},
    {'type':'single_choice','stem':'下列哪个不是Python的基本数据类型？',
     'options':{'A':'int','B':'str','C':'char','D':'bool'},'answer':'C','difficulty':1,'score':2,'kp_id':9,
     'tag_ids':[3]},
    {'type':'single_choice','stem':'下列关于递归函数的描述，错误的是？',
     'options':{'A':'必须有终止条件','B':'函数调用自身','C':'效率一定比迭代高','D':'可用于分治算法'},'answer':'C','difficulty':3,'score':2,'kp_id':19,
     'tag_ids':[4,10]},
    {'type':'single_choice','stem':'二分查找的时间复杂度是？',
     'options':{'A':'O(1)','B':'O(n)','C':'O(log n)','D':'O(n²)'},'answer':'C','difficulty':2,'score':2,'kp_id':19,
     'tag_ids':[4,9]},
    
    # 非选择题：代码填空 ×3
    {'type':'python_fill','stem':'完成以下选择排序代码：\n<pre>\ndef selection_sort(arr):\n    n = len(arr)\n    for i in range({{b1}}):\n        min_idx = i\n        for j in range({{b2}}, n):\n            if arr[j] < arr[min_idx]:\n                min_idx = j\n        arr[i], arr[min_idx] = arr[min_idx], arr[i]\n</pre>',
     'options':{},'answer':'','difficulty':3,'score':8,'kp_id':18,
     'blanks':[{'id':'b1','answer':'n-1','score':4},{'id':'b2','answer':'i+1','score':4}],
     'analysis':'<pre>外层循环n-1次，内层从i+1开始找最小值</pre>','tag_ids':[8]},
    
    {'type':'python_fill','stem':'完成以下二分查找代码：\n<pre>\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= {{b1}}:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = {{b2}}\n        else:\n            right = {{b3}}\n    return -1\n</pre>',
     'options':{},'answer':'','difficulty':3,'score':8,'kp_id':19,
     'blanks':[{'id':'b1','answer':'right','score':3},{'id':'b2','answer':'mid+1','score':3},{'id':'b3','answer':'mid-1','score':2}],
     'analysis':'二分查找每次将搜索区间减半','tag_ids':[9,4]},
    
    # Pandas题
    {'type':'pandas','stem':'给定学生成绩表 df，包含"姓名"、"班级"、"分数"列。请完成以下操作：\n(1) 按班级分组求平均分：{{b1}}\n(2) 筛选分数大于80的学生：{{b2}}',
     'options':{},'answer':'','difficulty':3,'score':7,'kp_id':22,
     'blanks':[{'id':'b1','answer':"df.groupby('班级')['分数'].mean()",'score':4},
               {'id':'b2','answer':"df[df['分数']>80]",'score':3}],
     'analysis':'<pre>df.groupby()用于分组聚合，df[条件]用于筛选</pre>','tag_ids':[2]},
    
    # 二叉树题
    {'type':'binary_tree','stem':'已知二叉树的前序遍历序列为 A B D E C F G，中序遍历序列为 D B E A F C G。\n(1) 画出该二叉树的结构（5分）\n(2) 写出后序遍历结果（2分）：{{b1}}',
     'options':{},'answer':'','difficulty':4,'score':7,'kp_id':35,
     'blanks':[{'id':'b1','answer':'DEBFGCA','score':2}],
     'analysis':'前序第一个A为根，中序中A左侧DBE为左子树，右侧FCG为右子树。递归求解。','tag_ids':[6,4]},
    
    # 流程图题
    {'type':'flowchart','stem':'下面是一个判断闰年的流程图，请分析并回答：\n<pre class="mermaid">\ngraph TD\n    A[输入年份y] --> B{y%4==0?}\n    B -->|否| C[非闰年]\n    B -->|是| D{y%100==0?}\n    D -->|否| E[闰年]\n    D -->|是| F{y%400==0?}\n    F -->|否| G[非闰年]\n    F -->|是| H[闰年]\n</pre>\n问：根据该流程图，1900年是否为闰年？答：{{b1}}（填"是"或"否"）',
     'options':{},'answer':'','difficulty':2,'score':15,'kp_id':14,
     'blanks':[{'id':'b1','answer':'否','score':15}],
     'analysis':'1900%4==0且1900%100==0但1900%400!=0，所以不是闰年。','tag_ids':[4]},
]

def seed():
    print(f"准备录入 {len(QUESTIONS)} 道试题...")
    success = 0
    for i, q in enumerate(QUESTIONS, 1):
        try:
            r = requests.post(f'{BASE}/api/questions', json=q)
            if r.status_code == 200 and r.json().get('ok'):
                success += 1
                print(f"  [{i}/{len(QUESTIONS)}] ✓ {q['type']} - {q['stem'][:30]}...")
            else:
                print(f"  [{i}/{len(QUESTIONS)}] ✗ {r.text[:100]}")
        except Exception as e:
            print(f"  [{i}/{len(QUESTIONS)}] ✗ 异常: {e}")
    print(f"\n✅ 成功录入 {success}/{len(QUESTIONS)} 道试题")

if __name__ == '__main__':
    seed()
