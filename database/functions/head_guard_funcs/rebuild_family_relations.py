"""把指定成员设为户主：重算全户成员与新户主的关系。

返回变更列表 [(member_name, old_rel, new_rel)]；不可确定的成员保持不变。
"""

from datetime import datetime

from ..._base import get_session
from ...models.person import Person
from .norm_relation import norm_relation
from .classify_relation import classify_relation
from .infer_gender import infer_gender
from .parent_rel import parent_rel
from .reverse_spouse import reverse_spouse
from .grandparent_rel import grandparent_rel
from .outer_grandparent_rel import outer_grandparent_rel
from .sibling_rel import sibling_rel
from .set_relation import set_relation
from .find_head import find_head
from .demoted_relation import demoted_relation


def rebuild_family_relations(hu_hao, new_head_id, new_head_old_relation):
    session = get_session()
    try:
        members = session.query(Person).filter_by(hu_hao=hu_hao).all()
        if not members:
            return []
        new_head = next((m for m in members if m.id == new_head_id), None)
        old_head = find_head(session, hu_hao, exclude_id=new_head_id)
        if not new_head or not old_head:
            return []
        old_rel = norm_relation(new_head_old_relation)
        category = classify_relation(old_rel)
        changes = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def set_rel(m, new_rel):
            set_relation(session, changes, now, m, new_rel)

        # 新户主原关系是旧户主的子女 -> 全户按"旧户主的血亲谱系"重推
        if category == 'child':
            set_rel(old_head, parent_rel(infer_gender(old_head.id_card)))
            for m in members:
                if m.id in (new_head_id, old_head.id):
                    continue
                c = classify_relation(m.relation)
                if c == 'spouse':            # 旧户主的配偶 -> 新户主的父/母
                    set_rel(m, parent_rel(infer_gender(m.id_card)))
                elif c == 'child':           # 旧户主的其他子女 -> 兄/弟/姐/妹
                    set_rel(m, sibling_rel(new_head, m))
                elif c == 'parent':          # 旧户主的父母 -> 祖父/祖母
                    set_rel(m, grandparent_rel(infer_gender(m.id_card)))
                elif c == 'inlaw_parent':    # 旧户主配偶的父母（岳父/岳母）-> 外祖父/外祖母
                    set_rel(m, outer_grandparent_rel(infer_gender(m.id_card)))
                # grand（孙辈归属不确定）、sibling（旁系）、other：保持
        # 新户主原关系是旧户主的配偶 -> 重推姻亲长辈，子女/孙辈保持
        elif category == 'spouse':
            set_rel(old_head, reverse_spouse(old_rel))
            n_gender = infer_gender(new_head.id_card)
            for m in members:
                if m.id in (new_head_id, old_head.id):
                    continue
                c = classify_relation(m.relation)
                if c == 'parent':            # 旧户主的父母
                    if n_gender == '女':     # 新户主是妻 -> 公婆
                        set_rel(m, '公公' if infer_gender(m.id_card) != '女' else '婆婆')
                    else:                    # 新户主是夫 -> 岳父/岳母
                        set_rel(m, '岳父' if infer_gender(m.id_card) != '女' else '岳母')
                elif c == 'inlaw_parent':    # 旧户主配偶的父母
                    if n_gender == '女':     # 新户主是妻 -> 该姻亲长辈即新户主父母
                        set_rel(m, parent_rel(infer_gender(m.id_card)))
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
