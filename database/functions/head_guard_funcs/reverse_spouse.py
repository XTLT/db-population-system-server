"""配偶反向：妻 <-> 夫。"""

from .norm_relation import norm_relation


def reverse_spouse(rel):
    rel = norm_relation(rel)
    if rel in ('妻', '妻子', '爱人'):
        return '夫'
    if rel in ('夫', '丈夫'):
        return '妻'
    return '配偶'
