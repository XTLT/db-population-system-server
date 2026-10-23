from datetime import datetime
from flask import request, jsonify

from database import get_session, update_person, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>', methods=['PUT'])
@require_auth
def api_update_person(person_id):
    """更新人员信息"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    client_updated_at = data.get('updated_at', '')
    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        if client_updated_at and p.updated_at and client_updated_at != p.updated_at:
            return jsonify({
                'error': 'conflict',
                'message': f'数据已被其他人修改！\n上次修改时间：{p.updated_at}\n您的修改时间：{client_updated_at}\n请刷新后重试。'
            }), 409
        
        # 身份证号不允许修改，防止数据完整性问题和身份欺诈
        if 'id_card' in data and data['id_card'] != p.id_card:
            return jsonify({'error': '身份证号不允许修改，如需更正请删除后重新添加'}), 400
        
        p.name = data.get('name', p.name)
        # 每户唯一户主：把某人改为"户主"时，整户关系按新户主自动重算
        # （旧户主降级 + 可确定的家庭其他成员关系联动；不确定的保持原值）
        new_relation = (data.get('relation') or '').strip() or p.relation
        if new_relation == '户主' and p.relation != '户主':
            from database.functions.head_guard import rebuild_family_relations
            rebuild_family_relations(p.hu_hao, p.id, p.relation)
        p.relation = new_relation
        p.phone = data.get('phone', p.phone)
        p.is_dead = data.get('is_dead', p.is_dead)
        p.address = data.get('address', p.address)
        p.group_name = data.get('group_name', p.group_name)
        p.poor_type = data.get('poor_type', p.poor_type)
        p.remark = data.get('remark', p.remark)
        p.disability = data.get('disability', p.disability)
        p.disability_type = data.get('disability_type', p.disability_type)
        p.dis_level = data.get('dis_level', p.dis_level)
        p.dibao = data.get('dibao', p.dibao)
        p.tekun = data.get('tekun', p.tekun)
        p.tekun_type = data.get('tekun_type', p.tekun_type)
        p.jisheng = data.get('jisheng', p.jisheng)
        p.social_card1 = data.get('social_card1', p.social_card1)
        new_land_area = data.get('land_area', p.land_area)
        old_land_area = p.land_area or ''
        
        # 只在已有土地面积发生变化时才要求填写原因（首次填写不要求）
        if new_land_area != old_land_area and old_land_area:
            land_reason = data.get('land_area_change_reason', '')
            if not land_reason:
                return jsonify({'error': '土地面积变更时必须填写变更原因'}), 400
            p.land_area = new_land_area
            p.land_area_change_reason = land_reason
            p.land_area_change_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_land_area != old_land_area:
            # 首次填写土地面积，不需要原因
            p.land_area = new_land_area
        new_local_welfare_forest_area = data.get('local_welfare_forest_area', p.local_welfare_forest_area)
        old_local_welfare_forest_area = p.local_welfare_forest_area or ''

        if new_local_welfare_forest_area != old_local_welfare_forest_area and old_local_welfare_forest_area:
            local_welfare_forest_reason = data.get('local_welfare_forest_change_reason', '')
            if not local_welfare_forest_reason:
                return jsonify({'error': '地方公益林变更时必须填写变更原因'}), 400
            p.local_welfare_forest_area = new_local_welfare_forest_area
            p.local_welfare_forest_change_reason = local_welfare_forest_reason
            p.local_welfare_forest_change_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_local_welfare_forest_area != old_local_welfare_forest_area:
            p.local_welfare_forest_area = new_local_welfare_forest_area
        new_national_welfare_forest_area = data.get('national_welfare_forest_area', p.national_welfare_forest_area)
        old_national_welfare_forest_area = p.national_welfare_forest_area or ''

        if new_national_welfare_forest_area != old_national_welfare_forest_area and old_national_welfare_forest_area:
            national_welfare_forest_reason = data.get('national_welfare_forest_change_reason', '')
            if not national_welfare_forest_reason:
                return jsonify({'error': '国家公益林变更时必须填写变更原因'}), 400
            p.national_welfare_forest_area = new_national_welfare_forest_area
            p.national_welfare_forest_change_reason = national_welfare_forest_reason
            p.national_welfare_forest_change_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_national_welfare_forest_area != old_national_welfare_forest_area:
            p.national_welfare_forest_area = new_national_welfare_forest_area
        new_commercial_forest_area = data.get('commercial_forest_area', p.commercial_forest_area)
        old_commercial_forest_area = p.commercial_forest_area or ''

        if new_commercial_forest_area != old_commercial_forest_area and old_commercial_forest_area:
            commercial_forest_reason = data.get('commercial_forest_change_reason', '')
            if not commercial_forest_reason:
                return jsonify({'error': '非国有天然商品林变更时必须填写变更原因'}), 400
            p.commercial_forest_area = new_commercial_forest_area
            p.commercial_forest_change_reason = commercial_forest_reason
            p.commercial_forest_change_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_commercial_forest_area != old_commercial_forest_area:
            p.commercial_forest_area = new_commercial_forest_area
        update_person(p)
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "修改人员",
            p.name,
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True, 'updated_at': p.updated_at})
    finally:
        session.close()
