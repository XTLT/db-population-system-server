from flask import jsonify

from database import get_session, Person
from utils.security import require_auth
from . import bp


@bp.route('/statistics/age_distribution')
@require_auth
def api_statistics_age_distribution():
    session = get_session()
    try:
        age_ranges = [
            ('0-18岁', 0, 18),
            ('19-59岁', 19, 59),
            ('60-80岁', 60, 80),
            ('80岁以上', 81, 200)
        ]
        
        all_ages = session.query(Person.age).filter(
            Person.age != '',
            Person.age.isnot(None)
        ).all()
        
        age_counts = {label: 0 for label, _, _ in age_ranges}
        
        for (age_str,) in all_ages:
            try:
                age = int(age_str)
                for label, min_age, max_age in age_ranges:
                    if min_age <= age <= max_age:
                        age_counts[label] += 1
                        break
            except (ValueError, TypeError):
                pass
        
        distribution = [
            {'range': label, 'count': age_counts[label]}
            for label, _, _ in age_ranges
        ]
        
        return jsonify({'distribution': distribution})
    finally:
        session.close()
