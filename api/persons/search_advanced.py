from flask import request, jsonify

from database import search_persons_advanced
from utils.security import require_auth
from . import bp


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
        'dis_level': p.dis_level or '',
        'dibao': p.dibao,
        'tekun': p.tekun or '',
        'tekun_type': p.tekun_type or '',
        'is_dead': p.is_dead,
        'is_migrated': p.is_migrated,
        'land_area': p.land_area or '',
        'local_welfare_forest_area': p.local_welfare_forest_area or '',
        'national_welfare_forest_area': p.national_welfare_forest_area or '',
        'commercial_forest_area': p.commercial_forest_area or ''
    } for p in persons])
