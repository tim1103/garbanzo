"""
浙江省高中信息技术学科知识点树
依据：浙江省普通高中信息技术学科课程标准
学考：必修1（数据与计算）+ 必修2（信息系统与社会）
选考：选择性必修1（数据与数据结构）+ 选择性必修2（网络基础）+ 选择性必修3（数据管理与分析）
"""

SEED_TREE = [
    {
        "code": "BX1",
        "name": "必修1：数据与计算",
        "book": "必修1",
        "children": [
            {"code": "BX1-1", "name": "数据与信息",
             "children": [
                 {"code": "BX1-1-1", "name": "数据的概念与特征"},
                 {"code": "BX1-1-2", "name": "信息的概念与特征"},
                 {"code": "BX1-1-3", "name": "知识的概念"},
                 {"code": "BX1-1-4", "name": "数据采集与编码"},
                 {"code": "BX1-1-5", "name": "进制转换（二/十/十六进制）"},
             ]},
            {"code": "BX1-2", "name": "算法与程序实现",
             "children": [
                 {"code": "BX1-2-1", "name": "算法的概念与特征"},
                 {"code": "BX1-2-2", "name": "流程图与程序框图"},
                 {"code": "BX1-2-3", "name": "Python基础语法（变量/输入输出/运算符）"},
                 {"code": "BX1-2-4", "name": "Python控制结构（顺序/分支/循环）"},
                 {"code": "BX1-2-5", "name": "Python函数与模块"},
                 {"code": "BX1-2-6", "name": "Python列表/字典/字符串"},
                 {"code": "BX1-2-7", "name": "解析算法与枚举算法"},
                 {"code": "BX1-2-8", "name": "排序算法（冒泡/选择/插入）"},
                 {"code": "BX1-2-9", "name": "查找算法（顺序/二分）"},
                 {"code": "BX1-2-10", "name": "迭代与递归算法"},
             ]},
            {"code": "BX1-3", "name": "数据处理与应用",
             "children": [
                 {"code": "BX1-3-1", "name": "Pandas基础（Series/DataFrame）"},
                 {"code": "BX1-3-2", "name": "数据读取与保存（CSV/Excel）"},
                 {"code": "BX1-3-3", "name": "数据筛选与排序"},
                 {"code": "BX1-3-4", "name": "数据分组与聚合（groupby）"},
                 {"code": "BX1-3-5", "name": "数据可视化（Matplotlib）"},
             ]},
        ]
    },
    {
        "code": "BX2",
        "name": "必修2：信息系统与社会",
        "book": "必修2",
        "children": [
            {"code": "BX2-1", "name": "信息系统组成与功能",
             "children": [
                 {"code": "BX2-1-1", "name": "信息系统概念"},
                 {"code": "BX2-1-2", "name": "信息系统组成要素"},
                 {"code": "BX2-1-3", "name": "信息系统功能"},
             ]},
            {"code": "BX2-2", "name": "计算机硬件与软件",
             "children": [
                 {"code": "BX2-2-1", "name": "计算机硬件组成"},
                 {"code": "BX2-2-2", "name": "操作系统基础"},
                 {"code": "BX2-2-3", "name": "移动终端"},
             ]},
            {"code": "BX2-3", "name": "网络基础",
             "children": [
                 {"code": "BX2-3-1", "name": "计算机网络概念与分类"},
                 {"code": "BX2-3-2", "name": "网络协议（TCP/IP、HTTP）"},
                 {"code": "BX2-3-3", "name": "IP地址与域名"},
                 {"code": "BX2-3-4", "name": "网络互联设备"},
             ]},
            {"code": "BX2-4", "name": "信息系统搭建（Flask）",
             "children": [
                 {"code": "BX2-4-1", "name": "Flask框架基础"},
                 {"code": "BX2-4-2", "name": "Flask路由与视图函数"},
                 {"code": "BX2-4-3", "name": "Flask模板渲染（Jinja2）"},
                 {"code": "BX2-4-4", "name": "Flask表单与请求处理"},
                 {"code": "BX2-4-5", "name": "Flask与SQLite数据库操作"},
             ]},
            {"code": "BX2-5", "name": "信息安全与社会责任",
             "children": [
                 {"code": "BX2-5-1", "name": "信息安全基础"},
                 {"code": "BX2-5-2", "name": "加密技术"},
                 {"code": "BX2-5-3", "name": "知识产权与道德规范"},
             ]},
        ]
    },
    {
        "code": "XXB1",
        "name": "选择性必修1：数据与数据结构",
        "book": "选择性必修1",
        "children": [
            {"code": "XXB1-1", "name": "数据结构基础",
             "children": [
                 {"code": "XXB1-1-1", "name": "数据结构概念"},
                 {"code": "XXB1-1-2", "name": "抽象数据类型"},
             ]},
            {"code": "XXB1-2", "name": "线性表",
             "children": [
                 {"code": "XXB1-2-1", "name": "数组与链表"},
                 {"code": "XXB1-2-2", "name": "链表结点操作（插入/删除）"},
                 {"code": "XXB1-2-3", "name": "栈与队列"},
             ]},
            {"code": "XXB1-3", "name": "树与图",
             "children": [
                 {"code": "XXB1-3-1", "name": "二叉树概念与性质"},
                 {"code": "XXB1-3-2", "name": "二叉树遍历（前/中/后/层序）"},
                 {"code": "XXB1-3-3", "name": "二叉排序树"},
                 {"code": "XXB1-3-4", "name": "图的概念与存储"},
                 {"code": "XXB1-3-5", "name": "图的遍历（DFS/BFS）"},
             ]},
            {"code": "XXB1-4", "name": "高级算法",
             "children": [
                 {"code": "XXB1-4-1", "name": "递归算法应用"},
                 {"code": "XXB1-4-2", "name": "分治算法"},
                 {"code": "XXB1-4-3", "name": "动态规划"},
                 {"code": "XXB1-4-4", "name": "贪心算法"},
             ]},
        ]
    },
    {
        "code": "XXB2",
        "name": "选择性必修2：网络基础",
        "book": "选择性必修2",
        "children": [
            {"code": "XXB2-1", "name": "网络体系结构",
             "children": [
                 {"code": "XXB2-1-1", "name": "OSI七层模型"},
                 {"code": "XXB2-1-2", "name": "TCP/IP四层模型"},
             ]},
            {"code": "XXB2-2", "name": "网络服务与应用",
             "children": [
                 {"code": "XXB2-2-1", "name": "Web服务与HTTP协议"},
                 {"code": "XXB2-2-2", "name": "DNS服务"},
                 {"code": "XXB2-2-3", "name": "电子邮件协议（SMTP/POP3）"},
                 {"code": "XXB2-2-4", "name": "FTP与文件传输"},
             ]},
            {"code": "XXB2-3", "name": "网络安全",
             "children": [
                 {"code": "XXB2-3-1", "name": "防火墙技术"},
                 {"code": "XXB2-3-2", "name": "加密与认证"},
             ]},
        ]
    },
    {
        "code": "XXB3",
        "name": "选择性必修3：数据管理与分析",
        "book": "选择性必修3",
        "children": [
            {"code": "XXB3-1", "name": "数据库基础",
             "children": [
                 {"code": "XXB3-1-1", "name": "数据库与数据库系统"},
                 {"code": "XXB3-1-2", "name": "关系模型与SQL"},
                 {"code": "XXB3-1-3", "name": "SQLite操作"},
             ]},
            {"code": "XXB3-2", "name": "数据分析方法",
             "children": [
                 {"code": "XXB3-2-1", "name": "数据清洗与预处理"},
                 {"code": "XXB3-2-2", "name": "统计分析与描述"},
                 {"code": "XXB3-2-3", "name": "Pandas高级操作"},
                 {"code": "XXB3-2-4", "name": "数据可视化进阶"},
             ]},
            {"code": "XXB3-3", "name": "大数据初步",
             "children": [
                 {"code": "XXB3-3-1", "name": "大数据概念与特征"},
                 {"code": "XXB3-3-2", "name": "大数据处理流程"},
             ]},
        ]
    },
]
