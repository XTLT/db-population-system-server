"""每户唯一户主守卫 + 换户主整户关系重建。

- find_head：查某户现有户主（可排除指定 id）
- rebuild_family_relations：把某人设为户主时，按该成员与户内其他成员的
  血亲/姻亲关系，自动重算全户成员与新户主的关系
  - 可确定的关系：父/母、兄/弟/姐/妹、祖父/祖母、外祖父/外祖母、公公/婆婆、岳父/岳母、夫/妻
  - 无法确定归属的（孙辈是谁的子女、儿媳是谁的妻）：保持原关系，不强行改错
- demote_old_head：保守场景（新户主与旧户主非直系/非配偶）只降级旧户主
"""

from datetime import datetime

from ..models.person import Person
from .._base import get_session

# ---------- 关系分类 ----------
CHILD_RELS = {'子', '女', '长子', '长女', '次子', '次女', '三子', '三女', '四女',
              '五女', '之子', '之女', '儿子', '女儿'}
SPOUSE_RELS = {'妻', '夫', '配偶', '妻子', '爱人', '丈夫'}
PARENT_RELS = {'父', '母亲', '父亲', '之父'}              # 旧户主的父母（血亲长辈）
INLAW_PARENT_RELS = {'岳父', '岳母', '公公', '婆婆'}        # 旧户主配偶的父母（姻亲长辈）
GRAND_RELS = {'孙子', '孙女', '外孙子', '外孙女', '之孙子', '之孙女', '之外孙女', '之孙子'}
SIBLING_RELS = {'兄', '弟', '姐', '妹', '姐姐', '妹妹'}

DEFAULT_DEMOTED = '其他'


def _norm(rel):
    return (rel or '').strip()


def infer_gender(id_card):
    """根据身份证号推断性别：'男' / '女' / ''"""
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


def _birth_key(id_card):
    """身份证出生日期字符串（用于比较长幼），取不到返回空。"""
    c = (id_card or '').strip()
    if len(c) == 18:
        return c[6:14]
    if len(c) == 15:
        return '19' + c[6:12]
    return ''


def _classify(rel):
    """把关系分类：child/spouse/parent/inlaw_parent/grand/sibling/other"""
    rel = _norm(rel)
    if rel in CHILD_RELS:
        return 'child'
    if rel in SPOUSE_RELS:
        return 'spouse'
    if rel in PARENT_RELS:
        return 'parent'
    if rel in INLAW_PARENT_RELS:
        return 'inlaw_parent'
    if rel in GRAND_RELS:
        return 'grand'
    if rel in SIBLING_RELS:
        return 'sibling'
    return 'other'


def _parent_rel(gender):
    return '父亲' if gender != '女' else '母亲'


def _reverse_spouse(rel):
    """配偶反向：妻<->夫"""
    rel = _norm(rel)
    if rel in ('妻', '妻子', '爱人'):
        return '夫'
    if rel in ('夫', '丈夫'):
        return '妻'
    return '配偶'


def _grandparent_rel(gender):
    """旧户主的父母在新户主（孙辈）视角下的关系：祖父/祖母（按该成员性别）"""
    return '祖父' if gender != '女' else '祖母'


def _outer_grandparent_rel(gender):
    return '外祖父' if gender != '女' else '外祖母'


def _sibling_rel(new_head, member):
    """同为旧户主子女的两个成员互为兄弟姐妹：按出生日期+性别定 兄/弟/姐/妹"""
    nk, mk = _birth_key(new_head.id_card), _birth_key(member.id_card)
    mg = infer_gender(member.id_card)
    if nk and mk:
        if nk < mk:
            return ('弟' if mg != '女' else '妹')   # member 比 new_head 小 -> 弟/妹
        if nk > mk:
            return ('兄' if mg != '女' else '姐')   # member 比 new_head 大 -> 兄/姐
    # 无出生日期时按原关系保留排行：原为长子/长女类保持原名，其他归兄弟姐妹类
    rel = _norm(member.relation)
    if rel in ('长子', '长女', '之子', '之女', '子', '女'):
        return rel if mg != '女' else ('姐' if rel in ('长女', '之女', '女') else '妹')
    return '弟' if mg != '女' else '妹'


def find_head(session, hu_hao, exclude_id=None):
    """查该户现有户主（排除指定 id）。无则返回 None。"""
    if not hu_hao:
        return None
    q = session.query(Person).filter_by(hu_hao=hu_hao, relation='户主')
    if exclude_id:
        q = q.filter(Person.id != exclude_id)
    return q.first()


def demoted_relation(new_head_old_relation, old_head_id_card):
    """（保守单降级用）新户主原关系 + 旧户主性别 -> 旧户主应降级的关系。"""
    rel = _norm(new_head_old_relation)
    gender = infer_gender(old_head_id_card)
    # 子女类
    if rel in CHILD_RELS:
        return _parent_rel(gender)
    # 姻亲晚辈
    if rel == '儿媳':
        return '公公' if gender != '女' else '婆婆'
    if rel == '女婿':
        return '岳父' if gender != '女' else '岳母'
    if rel in ('孙子', '孙女', '之孙子', '之孙女'):
        return '祖父' if gender != '女' else '祖母'
    if rel in ('外孙子', '外孙女', '之外孙女'):
        return '外祖父' if gender != '女' else '外祖母'
    if rel in SPOUSE_RELS:
        return _reverse_spouse(rel)
    if rel in PARENT_RELS:
        return _grandparent_rel(gender)
    return DEFAULT_DEMOTED


def rebuild_family_relations(hu_hao, new_head_id, new_head_old_relation):
    """把 new_head_id 设为户主：重算全户成员与新户主的关系。
    返回变更列表 [(member_name, old_rel, new_rel)]；不可确定的成员保持不变。
    """
    session = get_session()
    try:
        members = session.query(Person).filter_by(hu_hao=hu_hao).all()
        if not members:
            return []
        new_head = next((m for m in members if m.id == new_head_id), None)
        old_head = find_head(session, hu_hao, exclude_id=new_head_id)
        if not new_head or not old_head:
            return []
        old_rel = _norm(new_head_old_relation)
        category = _classify(old_rel)
        changes = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def set_rel(m, new_rel):
            cur = _norm(m.relation)
            if cur != new_rel:
                changes.append((m.name, cur, new_rel))
                m.relation = new_rel
                m.updated_at = now
                session.merge(m)

        # 新户主原关系是旧户主的子女 -> 全户按"旧户主的血亲谱系"重推
        if category == 'child':
            set_rel(old_head, _parent_rel(infer_gender(old_head.id_card)))
            for m in members:
                if m.id in (new_head_id, old_head.id):
                    continue
                c = _classify(m.relation)
                if c == 'spouse':            # 旧户主的配偶 -> 新户主的父/母
                    set_rel(m, _parent_rel(infer_gender(m.id_card)))
                elif c == 'child':           # 旧户主的其他子女 -> 兄/弟/姐/妹
                    set_rel(m, _sibling_rel(new_head, m))
                elif c == 'parent':          # 旧户主的父母 -> 祖父/祖母
                    set_rel(m, _grandparent_rel(infer_gender(m.id_card)))
                elif c == 'inlaw_parent':    # 旧户主配偶的父母（岳父/岳母）-> 外祖父/外祖母
                    set_rel(m, _outer_grandparent_rel(infer_gender(m.id_card)))
                # grand（孙辈归属不确定）、sibling（旁系）、other：保持
        # 新户主原关系是旧户主的配偶 -> 重推姻亲长辈，子女/孙辈保持
        elif category == 'spouse':
            set_rel(old_head, _reverse_spouse(old_rel))
            n_gender = infer_gender(new_head.id_card)
            for m in members:
                if m.id in (new_head_id, old_head.id):
                    continue
                c = _classify(m.relation)
                if c == 'parent':            # 旧户主的父母
                    if n_gender == '女':     # 新户主是妻 -> 公婆
                        set_rel(m, '公公' if infer_gender(m.id_card) != '女' else '婆婆')
                    else:                    # 新户主是夫 -> 岳父/岳母
                        set_rel(m, '岳父' if infer_gender(m.id_card) != '女' else '岳母')
                elif c == 'inlaw_parent':    # 旧户主配偶的父母
                    if n_gender == '女':     # 新户主是妻 -> 该姻亲长辈即新户主父母
                        set_rel(m, _parent_rel(infer_gender(m.id_card)))
                    # 新户主是夫且库中无旧户主配偶的"岳父岳母"，保持
        # 其他情况（新户主是旧户主的长辈/旁系）：保守只降级旧户主
        else:
            set_rel(old_head, demoted_relation(old_rel, old_head.id_card))

        session.commit()
        return changes
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def demote_old_head(hu_hao, exclude_id, new_head_old_relation):
    """保守单降级：把该户现有户主降级为匹配关系（兼容旧调用）。"""
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
