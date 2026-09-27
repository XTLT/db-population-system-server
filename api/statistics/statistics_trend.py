from datetime import datetime, timedelta
from flask import request, jsonify

from database import get_person_trend_data
from utils.security import require_auth
from . import bp


@bp.route('/statistics/trend')
@require_auth
def api_statistics_trend():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    group_by = request.args.get('group_by', 'month')
    
    if group_by not in ['day', 'week', 'month', 'year']:
        group_by = 'month'
    
    if not start_date or not end_date:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')
    
    try:
        data = get_person_trend_data(start_date, end_date, group_by)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
