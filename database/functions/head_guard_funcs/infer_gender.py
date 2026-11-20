"""根据身份证号推断性别：'男' / '女' / ''。"""


def infer_gender(id_card):
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
