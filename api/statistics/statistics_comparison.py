from flask import request, jsonify

from database import get_person_comparison
from utils.security import require_auth
from . import bp


@bp.route('/statistics/comparison')
@require_auth
def api_statistics_comparison():
    dimensions = request.args.getlist('dimensions')
    
    if not dimensions:
        dimensions = ['age', 'disability', 'dibao', 'migration', 'student']

    try:
        data = get_person_comparison(dimensions)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
