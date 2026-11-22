"""建房申请可写字段清单与常量。"""

APP_FIELDS = (
    'owner_name', 'owner_gender', 'owner_age', 'owner_phone', 'owner_id_card',
    'owner_hukou', 'hu_hao', 'group_name',
    'apply_land_area', 'building_area', 'cert_no',
    'current_disposal', 'current_disposal_other', 'current_land_area',
    'foundation_area', 'east_to', 'south_to', 'west_to', 'north_to',
    'build_type', 'land_type', 'house_floor_area', 'floors', 'building_height',
    'neighbor_opinion', 'design_plan', 'apply_reason',
    'village_opinion', 'village_leader', 'village_date',
    'applicant_signature', 'applicant_signature_at',
    'approval_land_area', 'approval_foundation_area', 'approval_address',
    'approval_build_type', 'approval_land_type', 'approval_house_floor_area',
    'approval_floors', 'approval_height',
    'status', 'remark',
)

AREA_FIELDS = {
    'apply_land_area': 'apply_area_num',
    'approval_land_area': 'approval_area_num',
}

MEMBER_FIELDS = ('seq', 'name', 'age', 'relation', 'id_card', 'hukou')

# 审批表五家机构（与 exports 里的标题一一对应）
APPROVAL_KEYS = ('natural', 'housing', 'agriculture', 'other', 'government')

APPROVAL_TITLES = {
    'natural': '乡镇承担自然资源职责的机构意见',
    'housing': '乡镇承担住房建设职责的机构意见',
    'agriculture': '乡镇承担农业农村职责的机构审查意见',
    'other': '其他机构部门审批意见',
    'government': '乡镇人民政府、街道办事处审批意见',
}

STATUS_LABELS = {'draft': '草稿', 'submitted': '已提交', 'approved': '已审批'}


def to_number(text):
    """把面积原文转成数值，容忍 '120.5m²'、'1,200'、全角数字等写法。"""
    if text is None:
        return 0.0
    s = str(text).strip()
    if not s:
        return 0.0
    s = s.replace(',', '').replace('，', '').replace('m²', '').replace('㎡', '')
    s = s.replace('平方米', '').replace('平米', '').replace(' ', '')
    s = s.translate(str.maketrans('０１２３４５６７８９．', '0123456789.'))
    try:
        return float(s)
    except ValueError:
        import re
        m = re.search(r'-?\d+(?:\.\d+)?', s)
        return float(m.group(0)) if m else 0.0
