from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from utils import escape_like
from . import bp


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
        if per_page < 1 or per_page > 10000:
            per_page = min(max(per_page, 1), 10000)  # 最大10000条（林地管理需全量）
        
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
                'group_name': p.group_name or '',
                'phone': p.phone or '',
                'is_dead': p.is_dead or '否',
                'disability': p.disability or '',
                'disability_type': p.disability_type or '',
                'dibao': p.dibao or '',
                'tekun': p.tekun or '',
                'tekun_type': p.tekun_type or '',
                'is_migrated': p.is_migrated or '否',
                'relation': p.relation or '',
                'land_area': p.land_area or '',
                'local_welfare_forest_area': p.local_welfare_forest_area or '',
                'national_welfare_forest_area': p.national_welfare_forest_area or '',
                'commercial_forest_area': p.commercial_forest_area or ''
            } for p in persons],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    finally:
        session.close()
