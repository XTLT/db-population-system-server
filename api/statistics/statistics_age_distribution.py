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
            ('19-30岁', 19, 30),
            ('31-40岁', 31, 40),
            ('41-50岁', 41, 50),
            ('51-60岁', 51, 60),
            ('60岁以上', 61, 200)
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
