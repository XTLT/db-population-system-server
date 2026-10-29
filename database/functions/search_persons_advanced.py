"""search_persons_advanced 函数。"""

from ..models.person import Person
from .._base import get_session

def search_persons_advanced(
    name: str = "",
    id_card: str = "",
    hu_hao: str = "",
    address: str = "",
    age_min: int = None,
    age_max: int = None,
    disability: str = "",
    dis_level: str = "",
    dibao: str = "",
    tekun: str = "",
    tekun_type: str = "",
    poor_type: str = "",
    relation: str = "",
    is_dead: str = "",
    limit: int = 100
) -> list:
    import re
    
    def escape_like(value: str) -> str:
        return re.sub(r'([%_])', r'\\\1', value)
    
    session = get_session()
    try:
        query = session.query(Person)
        
        # 应用筛选条件（使用参数化查询和转义）
        if name:
            escaped_name = escape_like(name)
            query = query.filter(Person.name.like(f"%{escaped_name}%", escape='\\'))
        
        if id_card:
            # 支持后6位查询
            if len(id_card) <= 6:
                escaped_id = escape_like(id_card)
                query = query.filter(Person.id_card.like(f"%{escaped_id}%", escape='\\'))
            else:
                query = query.filter(Person.id_card == id_card)
        
        if hu_hao:
            query = query.filter(Person.hu_hao == hu_hao)
        
        if address:
            escaped_address = escape_like(address)
            query = query.filter(Person.address.like(f"%{escaped_address}%", escape='\\'))
        
        if age_min is not None:
            query = query.filter(Person.age >= str(age_min))
        
        if age_max is not None:
            query = query.filter(Person.age <= str(age_max))
        
        if disability:
            if disability == '是':
                query = query.filter(Person.disability != '', Person.disability != '无')
            else:
                query = query.filter(Person.disability == disability)

        if dis_level:
            query = query.filter(Person.dis_level == dis_level)

        if dibao:
            # 支持逗号分隔多值（如 是,低保边缘家庭,特困家庭）
            dibao_values = [v.strip() for v in dibao.split(',') if v.strip()]
            # 与 statistics.py 的低保统计口径对齐：统计把以下 6 个值都计为“低保”。
            # 下钻传“是”时，展开为全部低保口径值（含 3 个历史值），保证统计数 == 下钻数。
            DIBAO_ALL = {'是', '低保边缘家庭', '特困家庭',
                         '最低生活保障家庭', '最低生活保障边缘家庭', '单人保家庭'}
            expanded = set()
            for v in dibao_values:
                if v == '是':
                    expanded |= DIBAO_ALL
                else:
                    expanded.add(v)
            query = query.filter(Person.dibao.in_(expanded))
        
        if tekun:
            query = query.filter(Person.tekun == tekun)
        
        if tekun_type:
            query = query.filter(Person.tekun_type == tekun_type)
        
        if poor_type:
            if poor_type == '一般户':
                # "一般户" = 户主未标记任何脱贫类型的户，库里存的是空值
                query = query.filter((Person.poor_type == '') | (Person.poor_type.is_(None)))
            else:
                query = query.filter(Person.poor_type == poor_type)
        
        if relation:
            query = query.filter(Person.relation == relation)
        
        if is_dead:
            query = query.filter(Person.is_dead == is_dead)
        
        return query.limit(limit).all()
    finally:
        session.close()

