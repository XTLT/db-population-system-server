import secrets
from flask import request, jsonify

from database import Person, add_person, add_operation_log, id_card_exists
from utils.security import require_auth
from utils.response import get_json_data
from utils import calculate_age, validate_id_card, validate_phone
from . import bp


@bp.route('/person', methods=['POST'])
@require_auth
def api_add_person():
    """添加人员"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err

    # 验证必填字段
    if not data.get('name'):
        return jsonify({'error': '姓名不能为空'}), 400
    
    # 验证身份证号格式
    id_card = data.get('id_card', '').strip()
    if id_card:
        valid, msg = validate_id_card(id_card)
        if not valid:
            return jsonify({'error': msg}), 400
    else:
        return jsonify({'error': '身份证号不能为空'}), 400

    # 检查身份证号是否已存在
    if id_card_exists(id_card):
        return jsonify({'error': '身份证号已存在'}), 400

    # 验证电话号码格式（如果提供）
    phone = data.get('phone', '')
    if phone:
        valid, msg = validate_phone(phone)
        if not valid:
            return jsonify({'error': f'电话号码: {msg}'}), 400

    # 如果户号为空，自动生成一个唯一户号
    hu_hao = data.get('hu_hao', '').strip()
    if not hu_hao:
        hu_hao = f"H{secrets.token_hex(4).upper()}"
        data['hu_hao'] = hu_hao

    # 使用随机ID替代可预测的身份证号ID
    person = Person(
        id=f"web_{secrets.token_hex(8)}",  # 随机ID，不可预测
        hu_hao=hu_hao,
        id_card=id_card,
        name=data['name'],
        age=calculate_age(id_card),
        address=data.get('address', ''),
        relation=data.get('relation', ''),
        phone=data.get('phone', ''),
        is_dead=data.get('is_dead', '否'),
        land_area=data.get('land_area', ''),
        local_welfare_forest_area=data.get('local_welfare_forest_area', ''),
        national_welfare_forest_area=data.get('national_welfare_forest_area', ''),
        commercial_forest_area=data.get('commercial_forest_area', ''),
        social_card1=data.get('social_card1', ''),
        poor_type=data.get('poor_type', ''),
        remark=data.get('remark', ''),
        disability=data.get('disability', ''),
        disability_type=data.get('disability_type', ''),
        dis_level=data.get('dis_level', ''),
        dibao=data.get('dibao', ''),
        tekun=data.get('tekun', ''),
        tekun_type=data.get('tekun_type', ''),
        jisheng=data.get('jisheng', ''),
    )
    add_person(person)
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "添加人员",
        data.get('name', ''),
        request.remote_addr,
        "Web"
    )
    return jsonify({'success': True})
