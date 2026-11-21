"""把 HouseBuildApp（含成员）序列化成前端用的扁平字典。"""

import json

from .fields import APPROVAL_KEYS


def _approvals(raw):
    data = {}
    if raw:
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            data = {}
    out = {}
    for key in APPROVAL_KEYS:
        item = data.get(key) or {}
        out[key] = {
            'opinion': item.get('opinion') or '',
            'leader': item.get('leader') or '',
            'date': item.get('date') or '',
        }
    return out


def serialize_app(app, members=None):
    if app is None:
        return None
    return {
        'id': app.id,
        'app_no': app.app_no or '',
        'person_id': app.person_id or '',
        'status': app.status or 'draft',
        'owner_name': app.owner_name or '',
        'owner_gender': app.owner_gender or '',
        'owner_age': app.owner_age or '',
        'owner_phone': app.owner_phone or '',
        'owner_id_card': app.owner_id_card or '',
        'owner_hukou': app.owner_hukou or '',
        'hu_hao': app.hu_hao or '',
        'group_name': app.group_name or '',
        'apply_land_area': app.apply_land_area or '',
        'apply_area_num': app.apply_area_num or 0.0,
        'building_area': app.building_area or '',
        'cert_no': app.cert_no or '',
        'current_disposal': app.current_disposal or '',
        'current_disposal_other': app.current_disposal_other or '',
        'current_land_area': app.current_land_area or '',
        'foundation_area': app.foundation_area or '',
        'east_to': app.east_to or '',
        'south_to': app.south_to or '',
        'west_to': app.west_to or '',
        'north_to': app.north_to or '',
        'build_type': app.build_type or '',
        'land_type': app.land_type or '',
        'house_floor_area': app.house_floor_area or '',
        'floors': app.floors or '',
        'building_height': app.building_height or '',
        'neighbor_opinion': app.neighbor_opinion or '',
        'design_plan': app.design_plan or '',
        'apply_reason': app.apply_reason or '',
        'village_opinion': app.village_opinion or '',
        'village_leader': app.village_leader or '',
        'village_date': app.village_date or '',
        'approval_land_area': app.approval_land_area or '',
        'approval_area_num': app.approval_area_num or 0.0,
        'approval_foundation_area': app.approval_foundation_area or '',
        'approval_address': app.approval_address or '',
        'approval_build_type': app.approval_build_type or '',
        'approval_land_type': app.approval_land_type or '',
        'approval_house_floor_area': app.approval_house_floor_area or '',
        'approval_floors': app.approval_floors or '',
        'approval_height': app.approval_height or '',
        'approvals': _approvals(app.approvals_json),
        'remark': app.remark or '',
        'created_at': app.created_at or '',
        'updated_at': app.updated_at or '',
        'created_by': app.created_by or '',
        'updated_by': app.updated_by or '',
        'members': [
            {
                'seq': m.seq or '',
                'name': m.name or '',
                'age': m.age or '',
                'relation': m.relation or '',
                'id_card': m.id_card or '',
                'hukou': m.hukou or '',
            }
            for m in (members or [])
        ],
    }
