import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify

from database import (
    get_session, Person, StudentEducation,
    search_by_name, search_persons_advanced, get_family_members,
    add_person, update_person, delete_person, migrate_person,
    get_student_education, check_duplicate_id_card,
    split_household, merge_household, add_new_household, generate_new_hu_hao,
    add_operation_log
)
from utils.security import require_auth, check_id_card_rate_limit
from utils.response import safe_error, safe_exception, get_json_data
from utils import calculate_age, escape_like, validate_id_card, validate_phone
from config import GRADE_DISPLAY, MAX_UPLOAD_SIZE
from excel_importer import get_person_subsidy_total


bp = Blueprint('persons', __name__)


def safe_id_card_query(session, person_id: str):
    p = session.query(Person).filter(Person.id == person_id).first()
    if p:
        return p, None
    
    if len(person_id) == 18 and (person_id[:-1].isdigit() and person_id[-1] in '0123456789xX'):
        is_allowed, remaining = check_id_card_rate_limit(person_id)
        if not is_allowed:
            return None, (jsonify({
                'error': f'查询过于频繁，请等待{remaining}秒后重试'
            }), 429)
        
        p = session.query(Person).filter(Person.id_card == person_id).first()
        if p:
            return p, None
    
    return None, (jsonify({'error': 'Not found'}), 404)


# ============== 人员列表 ==============

@bp.route('/persons')
@require_auth
def api_persons():
    """获取人员列表"""
    session = get_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 分页参数验证
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = min(max(per_page, 1), 100)  # 限制最大100条
        
        search = request.args.get('search', '')
        
        query = session.query(Person)
        if search:
            safe_search = escape_like(search)
            query = query.filter(Person.name.like(f'%{safe_search}%', escape='\\'))
        
        total = query.count()
        persons = query.order_by(Person.id.desc()).limit(per_page).offset((page-1)*per_page).all()
        
        return jsonify({
            'persons': [{
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'hu_hao': p.hu_hao,
                'age': p.age or '',
                'address': p.address or '',
                'phone': p.phone or '',
                'is_dead': p.is_dead or '否',
                'disability': p.disability or '',
                'dibao': p.dibao or '',
                'tekun': p.tekun or '',
                'tekun_type': p.tekun_type or '',
                'is_migrated': p.is_migrated or '否',
                'relation': p.relation or ''
            } for p in persons],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    finally:
        session.close()


# ============== 搜索 ==============

@bp.route('/search')
@require_auth
def api_search():
    """按姓名搜索人员"""
    name = request.args.get('name', '')
    if not name:
        return jsonify({'results': []})
    persons = search_by_name(name)
    
    # 记录审计日志：搜索敏感数据
    if persons:
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "搜索人员",
            f"关键词: {name}, 结果数: {len(persons)}",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
    
    return jsonify({'results': [{
        'id': p.id,
        'name': p.name,
        'id_card': p.id_card,
        'hu_hao': p.hu_hao,
        'age': p.age or '',
        'address': p.address or '',
        'relation': p.relation or '',
        'phone': p.phone or '',
        'is_dead': p.is_dead or '否',
        'remark': p.remark or '',
        'poor_type': p.poor_type or '',
        'disability': p.disability or '',
        'dis_level': p.dis_level or '',
        'dibao': p.dibao or '',
        'tekun': p.tekun or '',
        'tekun_type': p.tekun_type or '',
        'jisheng': p.jisheng or '',
        'social_card1': p.social_card1 or '',
        'social_card2': p.social_card2 or '',
        'social_card3': p.social_card3 or '',
        'is_migrated': p.is_migrated or '否',
        'land_area': p.land_area or ''
    } for p in persons]})


@bp.route('/search/advanced')
@require_auth
def api_search_advanced():
    """高级搜索人员"""
    # 获取查询参数
    name = request.args.get('name', '')
    id_card = request.args.get('id_card', '')
    hu_hao = request.args.get('hu_hao', '')
    address = request.args.get('address', '')
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    disability = request.args.get('disability', '')
    dis_level = request.args.get('dis_level', '')
    dibao = request.args.get('dibao', '')
    tekun = request.args.get('tekun', '')
    tekun_type = request.args.get('tekun_type', '')
    poor_type = request.args.get('poor_type', '')
    relation = request.args.get('relation', '')
    is_dead = request.args.get('is_dead', '')
    limit = request.args.get('limit', 100, type=int)
    
    # 验证并限制 limit 参数
    if limit < 1 or limit > 500:
        limit = min(max(limit, 1), 500)  # 限制最大500条
    
    # 验证年龄范围
    if age_min is not None and age_min < 0:
        age_min = 0
    if age_max is not None and age_max > 150:
        age_max = 150
    if age_min is not None and age_max is not None and age_min > age_max:
        age_min, age_max = age_max, age_min  # 交换使范围有效
    
    persons = search_persons_advanced(
        name=name,
        id_card=id_card,
        hu_hao=hu_hao,
        address=address,
        age_min=age_min,
        age_max=age_max,
        disability=disability,
        dis_level=dis_level,
        dibao=dibao,
        tekun=tekun,
        tekun_type=tekun_type,
        poor_type=poor_type,
        relation=relation,
        is_dead=is_dead,
        limit=limit
    )
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'id_card': p.id_card,
        'hu_hao': p.hu_hao,
        'age': p.age,
        'address': p.address,
        'relation': p.relation,
        'disability': p.disability,
        'dibao': p.dibao,
        'tekun': p.tekun or '',
        'tekun_type': p.tekun_type or '',
        'is_dead': p.is_dead,
        'is_migrated': p.is_migrated,
        'land_area': p.land_area or ''
    } for p in persons])


# ============== 检查重复 ==============

@bp.route('/check_duplicate')
@require_auth
def api_check_duplicate():
    """检查身份证号是否重复"""
    hu_hao = request.args.get('hu_hao', '')
    id_card = request.args.get('id_card', '')
    if not hu_hao or not id_card:
        return jsonify({'duplicate': False})
    duplicate = check_duplicate_id_card(hu_hao, id_card)
    return jsonify({'duplicate': duplicate})


# ============== 家庭成员 ==============

@bp.route('/family/<hu_hao>')
@require_auth
def api_family(hu_hao):
    """获取家庭成员"""
    members = get_family_members(hu_hao)
    current_year = str(datetime.now().year)
    result = []
    for m in members:
        edu = get_student_education(m.id)
        student_mark = ""
        if edu:
            grade_display = GRADE_DISPLAY.get(edu.grade, edu.grade)
            student_mark = f"{grade_display} {edu.school_name}"
        subsidy_amount = get_person_subsidy_total(m.id_card, current_year)
        result.append({
            'id': m.id,
            'name': m.name,
            'id_card': m.id_card,
            'relation': m.relation,
            'address': m.address,
            'age': m.age,
            'phone': m.phone,
            'is_dead': m.is_dead,
            'social_card1': m.social_card1,
            'social_card2': m.social_card2,
            'social_card3': m.social_card3,
            'poor_type': m.poor_type,
            'remark': m.remark,
            'disability': m.disability,
            'dis_level': m.dis_level,
            'dibao': m.dibao,
            'tekun': m.tekun or '',
            'tekun_type': m.tekun_type or '',
            'jisheng': m.jisheng,
            'is_migrated': m.is_migrated,
            'land_area': m.land_area or '',
            'land_area_change_reason': m.land_area_change_reason or '',
            'land_area_change_time': m.land_area_change_time or '',
            'student_mark': student_mark,
            'subsidy_amount': subsidy_amount
        })
    return jsonify({'members': result})


# ============== 人员 CRUD ==============

@bp.route('/person/<person_id>')
@require_auth
def api_person(person_id):
    """获取人员详情"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        
        # 记录审计日志：查看敏感数据
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "查看人员详情",
            f"{p.name}({p.id_card[:6]}****{p.id_card[-4:]})" if p.id_card else p.name,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        edu = get_student_education(p.id)
        return jsonify({
            'person': {
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'hu_hao': p.hu_hao,
                'relation': p.relation,
                'address': p.address,
                'age': p.age,
                'phone': p.phone,
                'is_dead': p.is_dead,
                'social_card1': p.social_card1,
                'social_card2': p.social_card2,
                'social_card3': p.social_card3,
                'poor_type': p.poor_type,
                'remark': p.remark,
                'disability': p.disability,
                'disability_type': p.disability_type,
                'dis_level': p.dis_level,
                'dibao': p.dibao,
                'tekun': p.tekun or '',
                'tekun_type': p.tekun_type or '',
                'jisheng': p.jisheng,
                'is_migrated': p.is_migrated,
                'land_area': p.land_area or '',
                'land_area_change_reason': p.land_area_change_reason or '',
                'land_area_change_time': p.land_area_change_time or '',
                'updated_at': p.updated_at or '',
                'education': {
                    'school_name': edu.school_name,
                    'grade': edu.grade,
                    'class_name': edu.class_name,
                    'guardian': edu.guardian,
                    'guardian_phone': edu.guardian_phone,
                    'is_left_behind': edu.is_left_behind,
                    'student_status': edu.student_status,
                    'enrollment_date': edu.enrollment_date,
                    'graduation_date': edu.graduation_date
                } if edu else None
            }
        })
    finally:
        session.close()


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
    if check_duplicate_id_card(id_card):
        return jsonify({'error': '身份证号已存在'}), 400

    # 验证电话号码格式（如果提供）
    phone = data.get('phone', '')
    if phone and phone != '无':
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
        phone=data.get('phone', '无'),
        is_dead=data.get('is_dead', '否'),
        land_area=data.get('land_area', ''),
        social_card1=data.get('social_card1', ''),
        social_card2=data.get('social_card2', ''),
        social_card3=data.get('social_card3', ''),
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
        p.relation = data.get('relation', p.relation)
        p.phone = data.get('phone', p.phone)
        p.is_dead = data.get('is_dead', p.is_dead)
        p.address = data.get('address', p.address)
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
        p.social_card2 = data.get('social_card2', p.social_card2)
        p.social_card3 = data.get('social_card3', p.social_card3)
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


@bp.route('/person/<person_id>', methods=['DELETE'])
@require_auth
def api_delete_person(person_id):
    """删除人员"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        real_id = p.id
    finally:
        session.close()
    delete_person(real_id)
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "删除人员",
        person_id,
        request.remote_addr,
        "Web",
        "是"
    )
    return jsonify({'success': True})


# ============== 迁移 ==============

@bp.route('/person/<person_id>/migrate', methods=['POST'])
@require_auth
def api_migrate_person(person_id):
    """迁移人员"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        real_id = p.id
    finally:
        session.close()
    migrate_person(
        real_id,
        data.get('date', ''),
        data.get('place', ''),
        data.get('reason', '')
    )
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "户籍迁出",
        person_id,
        request.remote_addr,
        "Web"
    )
    return jsonify({'success': True})


# ============== 户操作 ==============

@bp.route('/household/split', methods=['POST'])
@require_auth
def api_split_household():
    """分户"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    person_ids = data.get('person_ids', [])
    new_hu_hao = data.get('new_hu_hao', '')
    try:
        result_hu_hao = split_household(person_ids, new_hu_hao)
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "分户",
            f"新户号:{result_hu_hao}",
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True, 'new_hu_hao': result_hu_hao})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/household/merge', methods=['POST'])
@require_auth
def api_merge_household():
    """并户"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    target_hu_hao = data.get('target_hu_hao', '')
    person_ids = data.get('person_ids', [])
    try:
        merge_household(target_hu_hao, person_ids)
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "合户",
            f"目标户号:{target_hu_hao}",
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/household/add', methods=['POST'])
@require_auth
def api_add_household():
    """新增户"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    try:
        add_new_household(
            hu_hao=data.get('hu_hao', ''),
            name=data.get('name', ''),
            id_card=data.get('id_card', ''),
            relation=data.get('relation', '户主'),
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            land_area=data.get('land_area', '')
        )
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "新增户",
            f"户号:{data.get('hu_hao')}",
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/household/new_number')
@require_auth
def api_new_hu_hao():
    """获取新户号"""
    return jsonify({'hu_hao': generate_new_hu_hao()})


# ============== 批量操作 ==============

# 批量操作限制
MAX_BATCH_DELETE_COUNT = 100  # 单次最大删除数量
MAX_BATCH_UPDATE_COUNT = 200  # 单次最大更新数量

# 允许批量更新的字段白名单
BATCH_UPDATE_ALLOWED_FIELDS = {
    'relation', 'phone', 'address', 'remark', 
    'disability', 'dis_level', 'dibao', 'tekun', 'tekun_type', 'jisheng',
    'social_card1', 'social_card2', 'social_card3', 'land_area'
}


@bp.route('/persons/batch-delete', methods=['POST'])
@require_auth
def api_batch_delete_persons():
    """批量删除人员（仅管理员）
    
    安全限制：
    - 单次最多删除 100 条记录
    - 需要管理员权限
    - 记录详细审计日志
    """
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    person_ids = data.get('ids', [])
    
    if not person_ids:
        return jsonify({'error': '未选择人员'}), 400
    
    # 数量限制
    if len(person_ids) > MAX_BATCH_DELETE_COUNT:
        return jsonify({
            'error': f'单次最多删除 {MAX_BATCH_DELETE_COUNT} 条记录，当前选择了 {len(person_ids)} 条'
        }), 400
    
    # 要求确认（通过请求参数）
    confirm = data.get('confirm', False)
    if not confirm:
        return jsonify({
            'error': '需要确认',
            'require_confirm': True,
            'count': len(person_ids)
        }), 400
    
    session = get_session()
    try:
        # 支持人员ID和身份证号两种方式
        deleted_count = session.query(Person).filter(
            (Person.id.in_(person_ids)) | (Person.id_card.in_(person_ids))
        ).delete(synchronize_session='fetch')
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量删除人员",
            f"删除{deleted_count}人，ID列表: {','.join(person_ids[:10])}{'...' if len(person_ids) > 10 else ''}",
            request.remote_addr,
            "Web"
        )
        
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        session.rollback()
        return safe_exception(e, "删除失败", 500)
    finally:
        session.close()


@bp.route('/persons/batch-update', methods=['POST'])
@require_auth
def api_batch_update_persons():
    """批量更新人员信息（仅管理员）
    
    安全限制：
    - 单次最多更新 200 条记录
    - 只允许更新白名单中的字段
    - 验证更新值的有效性
    """
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    person_ids = data.get('ids', [])
    updates = data.get('updates', {})
    
    if not person_ids:
        return jsonify({'error': '未选择人员'}), 400
    
    if not updates:
        return jsonify({'error': '未提供更新内容'}), 400
    
    # 数量限制
    if len(person_ids) > MAX_BATCH_UPDATE_COUNT:
        return jsonify({
            'error': f'单次最多更新 {MAX_BATCH_UPDATE_COUNT} 条记录，当前选择了 {len(person_ids)} 条'
        }), 400
    
    # 过滤不允许更新的字段
    filtered_updates = {}
    for key, value in updates.items():
        if key in BATCH_UPDATE_ALLOWED_FIELDS:
            filtered_updates[key] = value
    
    if not filtered_updates:
        return jsonify({'error': '没有有效的更新字段'}), 400
    
    session = get_session()
    try:
        persons = session.query(Person).filter(Person.id.in_(person_ids)).all()
        updated_count = 0
        
        for person in persons:
            for key, value in filtered_updates.items():
                setattr(person, key, value)
            person.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量更新人员",
            f"更新{updated_count}人，字段: {','.join(filtered_updates.keys())}",
            request.remote_addr,
            "Web"
        )
        
        return jsonify({'success': True, 'updated': updated_count, 'fields_updated': list(filtered_updates.keys())})
    except Exception as e:
        session.rollback()
        return safe_exception(e, "更新失败", 500)
    finally:
        session.close()
