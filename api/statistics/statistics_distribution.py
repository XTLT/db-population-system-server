from flask import request, jsonify

from database import get_person_distribution, Person
from utils.security import require_auth
from . import bp


@bp.route('/statistics/distribution')
@require_auth
def api_statistics_distribution():
    field = request.args.get('field', '')
    
    if not field:
        return jsonify({'error': '缺少field参数'}), 400
    
    valid_fields = ['disability', 'dibao', 'age_group', 'gender']
    if field not in valid_fields and not hasattr(Person, field):
        return jsonify({'error': f'无效的field参数，支持: {", ".join(valid_fields)}'}), 400
    
    try:
        data = get_person_distribution(field)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
