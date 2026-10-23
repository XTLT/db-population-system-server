"""每户唯一户主守卫：换户主时自动降级旧户主。

- find_head：查某户现有户主（可排除指定 id）
- demote_old_head：把旧户主降级为与家庭成员关系匹配的关系
- 添加人员时 relation='户主' 且该户已有户主 → 由 add_person API 拒绝
- 修改人员关系为 '户主' 时 → 由 update_person API 调用 demote_old_head 自动降级
"""

from datetime import datetime

from ..models.person import Person
from .._base import get_session

# 新户主原来的关系 -> (旧户主为男, 旧户主为女) 的降级关系
# 例：儿子 改为户主后，旧户主（男）自动变为 父亲、（女）自动变为 母亲
DEMOTE_MAP = {
    '儿子': ('父亲', '母亲'),
    '长子': ('父亲', '母亲'),
    '次子': ('父亲', '母亲'),
    '三子': ('父亲', '母亲'),
    '女儿': ('父亲', '母亲'),
    '长女': ('父亲', '母亲'),
    '次女': ('父亲', '母亲'),
    '三女': ('父亲', '母亲'),
    '儿媳': ('公公', '婆婆'),
    '女婿': ('岳父', '岳母'),
    '孙子': ('祖父', '祖母'),
    '孙女': ('祖父', '祖母'),
    '外孙': ('外祖父', '外祖母'),
    '外孙女': ('外祖父', '外祖母'),
    '外孙子女': ('外祖父', '外祖母'),
    '妻子': ('丈夫', '丈夫'),
    '爱人': ('丈夫', '丈夫'),
    '配偶': ('丈夫', '妻子'),
    '夫': ('妻子', '妻子'),
    '丈夫': ('妻子', '妻子'),
    '父亲': ('父亲', '父亲'),
    '母亲': ('母亲', '母亲'),
    '祖父': ('祖父', '祖父'),
    '祖母': ('祖母', '祖母'),
}
DEFAULT_DEMOTED = '其他'


def infer_gender(id_card: str) -> str:
    """根据身份证号推断性别：'男' / '女' / ''（无法判断时为空）"""
    if not id_card:
        return ''
    id_card = id_card.strip()
    try:
        if len(id_card) == 18:
            return '男' if int(id_card[16]) % 2 == 1 else '女'
        if len(id_card) == 15:
            return '男' if int(id_card[14]) % 2 == 1 else '女'
    except (ValueError, TypeError):
        pass
    return ''


def find_head(session, hu_hao, exclude_id=None):
    """查该户现有户主（排除指定 id）。无则返回 None。"""
    if not hu_hao:
        return None
    q = session.query(Person).filter_by(hu_hao=hu_hao, relation='户主')
    if exclude_id:
        q = q.filter(Person.id != exclude_id)
    return q.first()


def demoted_relation(new_head_old_relation, old_head_id_card):
    """新户主原来的关系 + 旧户主性别 -> 旧户主应降级为的关系。"""
    pair = DEMOTE_MAP.get((new_head_old_relation or '').strip())
    if not pair:
        return DEFAULT_DEMOTED
    return pair[0] if infer_gender(old_head_id_card) != '女' else pair[1]


def demote_old_head(hu_hao, exclude_id, new_head_old_relation):
    """把该户现有户主降级为匹配关系。返回被降级的旧户主（Person）或 None。"""
    session = get_session()
    try:
        old_head = find_head(session, hu_hao, exclude_id=exclude_id)
        if old_head is None:
            return None
        old_head.relation = demoted_relation(new_head_old_relation, old_head.id_card)
        old_head.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.merge(old_head)
        session.commit()
        return old_head
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
