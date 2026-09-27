"""generate_report_data 函数。"""

from ..models.student_education import StudentEducation
from ..models.land_subsidy import LandSubsidy
from .._base import get_session
from .get_person_distribution import get_person_distribution
from .get_person_trend_data import get_person_trend_data
from .get_person_comparison import get_person_comparison
from .get_person_count import get_person_count

def generate_report_data(report_type: str, dimensions: list, 
                         date_range: dict = None, filters: dict = None) -> dict:
    pass
    
    start_date = date_range.get('start', '') if date_range else ''
    end_date = date_range.get('end', '') if date_range else ''
    
    result = {
        'report_type': report_type,
        'dimensions': dimensions,
        'date_range': date_range or {},
        'filters': filters or {},
        'labels': [],
        'values': [],
        'summary': {},
        'total': 0
    }
    
    if report_type == 'person':
        # 人员统计报表
        for dim in dimensions:
            if dim == 'age_group':
                data = get_person_distribution('age_group')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'gender':
                data = get_person_distribution('gender')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'disability':
                data = get_person_distribution('disability')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'dibao':
                data = get_person_distribution('dibao')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'tekun':
                data = get_person_distribution('tekun')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'trend':
                group_by = filters.get('group_by', 'month') if filters else 'month'
                data = get_person_trend_data(start_date, end_date, group_by)
                result['labels'] = data.get('labels', [])
                result['values'] = [
                    data.get('additions', []),
                    data.get('deletions', [])
                ]
                result['summary'][dim] = data
            elif dim == 'comparison':
                data = get_person_comparison(dimensions)
                result['labels'] = data.get('dimensions', [])
                result['values'] = data.get('values', [])
                result['summary'][dim] = data
        
        # 获取总数
        result['total'] = get_person_count()
    
    elif report_type == 'student':
        # 学生统计报表
        session = get_session()
        try:
            pass
            
            # 应用筛选条件
            query = session.query(StudentEducation)
            if filters:
                if filters.get('school'):
                    query = query.filter(StudentEducation.school_name == filters['school'])
                if filters.get('grade'):
                    query = query.filter(StudentEducation.grade == filters['grade'])
                if filters.get('is_left_behind'):
                    query = query.filter(StudentEducation.is_left_behind == filters['is_left_behind'])
            
            students = query.filter(
                StudentEducation.student_status.in_(['在读', '跳级', '留级'])
            ).all()
            
            result['total'] = len(students)
            
            for dim in dimensions:
                if dim == 'grade':
                    # 年级分布
                    grade_counts = {}
                    for s in students:
                        grade = s.grade or '未知'
                        grade_counts[grade] = grade_counts.get(grade, 0) + 1
                    result['labels'] = list(grade_counts.keys())
                    result['values'] = list(grade_counts.values())
                    result['summary'][dim] = grade_counts
                
                elif dim == 'school':
                    # 学校分布
                    school_counts = {}
                    for s in students:
                        school = s.school_name or '未知'
                        school_counts[school] = school_counts.get(school, 0) + 1
                    result['labels'] = list(school_counts.keys())
                    result['values'] = list(school_counts.values())
                    result['summary'][dim] = school_counts
                
                elif dim == 'left_behind':
                    # 留守儿童分布
                    lb_counts = {'留守儿童': 0, '非留守儿童': 0}
                    for s in students:
                        if s.is_left_behind == '是':
                            lb_counts['留守儿童'] += 1
                        else:
                            lb_counts['非留守儿童'] += 1
                    result['labels'] = list(lb_counts.keys())
                    result['values'] = list(lb_counts.values())
                    result['summary'][dim] = lb_counts
        
        finally:
            session.close()
    
    elif report_type == 'subsidy':
        # 补贴统计报表
        session = get_session()
        try:
            pass
            
            query = session.query(LandSubsidy)
            
            # 应用日期筛选
            if start_date:
                query = query.filter(LandSubsidy.year >= start_date[:4])
            if end_date:
                query = query.filter(LandSubsidy.year <= end_date[:4])
            
            subsidies = query.all()
            result['total'] = len(subsidies)
            
            for dim in dimensions:
                if dim == 'year':
                    # 年度分布
                    year_counts = {}
                    year_amounts = {}
                    for s in subsidies:
                        year = s.subsidy_year or '未知'
                        year_counts[year] = year_counts.get(year, 0) + 1
                        amount = float(s.total_amount) if s.total_amount else 0
                        year_amounts[year] = year_amounts.get(year, 0) + amount
                    result['labels'] = list(year_counts.keys())
                    result['values'] = list(year_amounts.values())
                    result['summary'][dim] = {
                        'counts': year_counts,
                        'amounts': year_amounts
                    }
                
                elif dim == 'amount_distribution':
                    # 金额分布
                    amount_ranges = {
                        '0-500': 0,
                        '500-1000': 0,
                        '1000-2000': 0,
                        '2000以上': 0
                    }
                    for s in subsidies:
                        try:
                            amount = float(s.total_amount) if s.total_amount else 0
                            if amount < 500:
                                amount_ranges['0-500'] += 1
                            elif amount < 1000:
                                amount_ranges['500-1000'] += 1
                            elif amount < 2000:
                                amount_ranges['1000-2000'] += 1
                            else:
                                amount_ranges['2000以上'] += 1
                        except Exception:
                            pass
                    result['labels'] = list(amount_ranges.keys())
                    result['values'] = list(amount_ranges.values())
                    result['summary'][dim] = amount_ranges
        
        finally:
            session.close()
    
    return result

