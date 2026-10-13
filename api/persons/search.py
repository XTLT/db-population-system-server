from flask import request, jsonify

from database import search_by_name, add_operation_log
from utils.security import require_auth
from . import bp


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
        'group_name': p.group_name or '',
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
        'social_card2_source': p.social_card2_source or '',
        'social_card3_source': p.social_card3_source or '',
        'is_migrated': p.is_migrated or '否',
        'land_area': p.land_area or '',
        'local_welfare_forest_area': p.local_welfare_forest_area or '',
        'national_welfare_forest_area': p.national_welfare_forest_area or '',
        'commercial_forest_area': p.commercial_forest_area or ''
    } for p in persons]})
