"""关系字段去空格。"""


def norm_relation(rel):
    return (rel or '').strip()
