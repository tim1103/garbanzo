"""
试卷模板预设
"""
TEMPLATES = {
    'xuekao': {
        'name': '学考卷（50分）',
        'total_score': 50,
        'single_choice': {
            'count': 10,
            'per_score': 2,
        },
        'non_choice': [
            {'type': 'python_fill', 'count': 1, 'per_score': 15},
            {'type': 'flowchart', 'count': 1, 'per_score': 15},
        ],
    },
    'xuankao': {
        'name': '选考卷（50分）',
        'total_score': 50,
        'single_choice': {
            'count': 12,
            'per_score': 2,
        },
        'non_choice': [
            {'type': 'python_fill', 'count': 1, 'per_score': 8},
            {'type': 'pandas', 'count': 1, 'per_score': 7},
            {'type': 'binary_tree', 'count': 1, 'per_score': 7},
        ],
    }
}
