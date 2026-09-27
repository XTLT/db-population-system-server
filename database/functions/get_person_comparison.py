"""get_person_comparison 函数。"""

from ..models.person import Person
from ..models.student_education import StudentEducation
from .._base import get_session

def get_person_comparison(dimensions: list) -> dict:
    from sqlalchemy import func
    
    session = get_session()
    try:
        total = session.query(func.count(Person.id)).scalar() or 1
        
        result = {
            'dimensions': [],
            'values': [],
            'raw_values': [],
            'total': total
        }
        
        for dim in dimensions:
            count = 0
            
            if dim == 'age':
                # 平均年龄
                persons = session.query(Person.age).all()
                ages = []
                for p in persons:
                    try:
                        if p.age:
                            ages.append(int(p.age))
                    except Exception:
                        pass
                
                if ages:
                    avg_age = sum(ages) / len(ages)
                    # 归一化：假设最大年龄100
                    normalized = min(100, (avg_age / 100) * 100)
                    count = avg_age
                else:
                    normalized = 0
                    count = 0
                
                result['dimensions'].append('平均年龄')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(round(count, 1))
            
            elif dim == 'disability':
                # 残疾人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.disability != '',
                    Person.disability != '无'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('残疾人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'dibao':
                # 低保人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.dibao != '',
                    Person.dibao != '无'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('低保人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'tekun':
                # 特困供养人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.tekun != '',
                    Person.tekun != '无'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('特困供养人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'migration':
                # 迁出人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.is_migrated == '是'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('迁出人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'death':
                # 去世人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.is_dead == '是'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('去世人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'student':
                # 在读学生比例
                count = session.query(func.count(StudentEducation.id)).filter(
                    StudentEducation.student_status.in_(['在读', '跳级', '留级'])
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('在读学生')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'gender_male':
                # 男性比例
                persons = session.query(Person.id_card).all()
                male = 0
                for p in persons:
                    if p.id_card and len(p.id_card) >= 2:
                        try:
                            gender_digit = int(p.id_card[-2])
                            if gender_digit % 2 == 1:
                                male += 1
                        except Exception:
                            pass
                normalized = (male / total) * 100
                
                result['dimensions'].append('男性比例')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(male)
            
            elif dim == 'gender_female':
                # 女性比例
                persons = session.query(Person.id_card).all()
                female = 0
                for p in persons:
                    if p.id_card and len(p.id_card) >= 2:
                        try:
                            gender_digit = int(p.id_card[-2])
                            if gender_digit % 2 == 0:
                                female += 1
                        except Exception:
                            pass
                normalized = (female / total) * 100
                
                result['dimensions'].append('女性比例')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(female)
            
            else:
                # 默认统计非空值
                if hasattr(Person, dim):
                    count = session.query(func.count(Person.id)).filter(
                        getattr(Person, dim) != '',
                        getattr(Person, dim) != '无'
                    ).scalar() or 0
                    normalized = (count / total) * 100
                    
                    result['dimensions'].append(dim)
                    result['values'].append(round(normalized, 2))
                    result['raw_values'].append(count)
        
        return result
    finally:
        session.close()

