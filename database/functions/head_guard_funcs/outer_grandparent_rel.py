"""旧户主配偶的父母在新户主视角下的关系：外祖父 / 外祖母。"""


def outer_grandparent_rel(gender):
    return '外祖父' if gender != '女' else '外祖母'
