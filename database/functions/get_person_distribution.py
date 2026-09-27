"""get_person_distribution 函数。"""

from ..models.person import Person
from .._base import get_session

def get_person_distribution(field: str) -> dict:
    from sqlalchemy import func
    
    session = get_session()
    try:
        result = {}
        
        if field == 'disability':
            # 残疾情况分布
            counts = session.query(
                Person.disability,
                func.count(Person.id).label('count')
            ).group_by(Person.disability).all()
            
            for disability, count in counts:
                label = disability if disability else '无'
                result[label] = count
        
        elif field == 'dibao':
            # 低保情况分布
            counts = session.query(
                Person.dibao,
                func.count(Person.id).label('count')
            ).group_by(Person.dibao).all()
            
            for dibao, count in counts:
                label = dibao if dibao else '无'
                result[label] = count
        
        elif field == 'tekun':
            # 特困供养情况分布
            counts = session.query(
                Person.tekun,
                func.count(Person.id).label('count')
            ).group_by(Person.tekun).all()
            
            for tekun, count in counts:
                label = tekun if tekun else '无'
                result[label] = count
        
        elif field == 'age_group':
            # 年龄段分布
            persons = session.query(Person.age).all()
            
            age_groups = {
                '0-17岁': 0,
                '18-35岁': 0,
                '36-50岁': 0,
                '51-65岁': 0,
                '66-80岁': 0,
                '80岁以上': 0
            }
            
            for p in persons:
                try:
                    age = int(p.age) if p.age else 0
                    if age <= 17:
                        age_groups['0-17岁'] += 1
                    elif age <= 35:
                        age_groups['18-35岁'] += 1
                    elif age <= 50:
                        age_groups['36-50岁'] += 1
                    elif age <= 65:
                        age_groups['51-65岁'] += 1
                    elif age <= 80:
                        age_groups['66-80岁'] += 1
                    else:
                        age_groups['80岁以上'] += 1
                except Exception:
                    age_groups['0-17岁'] += 1
            
            result = age_groups
        
        elif field == 'gender':
            # 性别分布（从身份证号推断）
            persons = session.query(Person.id_card).all()
            
            male = 0
            female = 0
            unknown = 0
            
            for p in persons:
                if p.id_card and len(p.id_card) >= 2:
                    try:
                        # 身份证倒数第二位：奇数为男，偶数为女
                        gender_digit = int(p.id_card[-2])
                        if gender_digit % 2 == 1:
                            male += 1
                        else:
                            female += 1
                    except Exception:
                        unknown += 1
                else:
                    unknown += 1
            
            result = {
                '男性': male,
                '女性': female
            }
            if unknown > 0:
                result['未知'] = unknown
        
        else:
            # 通用字段统计
            if hasattr(Person, field):
                counts = session.query(
                    getattr(Person, field),
                    func.count(Person.id).label('count')
                ).group_by(getattr(Person, field)).all()
                
                for value, count in counts:
                    label = value if value else '无'
                    result[label] = count
        
        return result
    finally:
        session.close()

