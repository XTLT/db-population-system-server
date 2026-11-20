"""旧户主的父母在新户主（孙辈）视角下的关系：祖父 / 祖母。"""


def grandparent_rel(gender):
    return '祖父' if gender != '女' else '祖母'
