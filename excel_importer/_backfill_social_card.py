from utils import safe_str

def _backfill_social_card(person, source_remark, card_number):
    """方案C：社保卡2/3 自动回填。
    规则：
    - 卡号为空：跳过
    - 卡号与 1/2/3 任一相同：跳过（卡号相同不重复占用，含手动输入的卡1）
    - 来源与2相同：更新2的卡号（来源不变）；与3相同：更新3
    - 2空 → 写入2并记来源；3空 → 写入3并记来源
    - 2、3 均被不同来源占用 → 覆盖最早的（槽2），同时更新来源
    """
    card = safe_str(card_number).strip()
    if not card:
        return
    cur = [safe_str(getattr(person, c, "")).strip()
           for c in ("social_card1", "social_card2", "social_card3")]
    if card in cur:
        return
    src2 = safe_str(getattr(person, "social_card2_source", "")).strip()
    src3 = safe_str(getattr(person, "social_card3_source", "")).strip()
    if src2 == source_remark:
        person.social_card2 = card
    elif src3 == source_remark:
        person.social_card3 = card
    elif not src2:
        person.social_card2 = card
        person.social_card2_source = source_remark
    elif not src3:
        person.social_card3 = card
        person.social_card3_source = source_remark
    else:
        person.social_card2 = card
        person.social_card2_source = source_remark
