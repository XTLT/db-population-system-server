"""把到龄人员列表排成便于照着办手续的正文。"""

from .age_notification_cache import MAX_LINES


def format_age_content(persons):
    lines = []
    for idx, p in enumerate(persons[:MAX_LINES], 1):
        id_card = p.id_card or ""
        birthday = ""
        if len(id_card) >= 14:
            birthday = "%s-%s-%s" % (id_card[6:10], id_card[10:12], id_card[12:14])
        where = " ".join(x for x in (p.group_name, p.address) if x)
        phone = ("  电话 %s" % p.phone) if p.phone else ""
        lines.append("%d. %s  %s  %s  生日 %s%s" % (idx, p.name or "", id_card, where, birthday, phone))
    if len(persons) > MAX_LINES:
        lines.append("…… 共 %d 人，此处只列前 %d 条，完整名单请按生日到人员查询里筛" % (len(persons), MAX_LINES))
    return "\n".join(lines)
