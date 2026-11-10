from utils.security import get_client_ip
from flask import request, jsonify

from database import (
    get_session, get_student_education, add_operation_log,
    DibaoPayment, DisabilityCarePayment, ElderlyAllowance,
    LandSubsidy, PensionInsurance, TekunPayment,
)
from utils.security import require_auth
from config import GRADE_DISPLAY
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>')
@require_auth
def api_person(person_id):
    """获取人员详情"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        
        # 记录审计日志：查看敏感数据
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "查看人员详情",
            f"{p.name}({p.id_card[:6]}****{p.id_card[-4:]})" if p.id_card else p.name,
            get_client_ip(),
            request.headers.get('X-Client-Type', 'Web')
        )
        
        edu = get_student_education(p.id)
        return jsonify({
            'person': {
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'hu_hao': p.hu_hao,
                'relation': p.relation,
                'address': p.address,
                'group_name': p.group_name or '',
                'age': p.age,
                'phone': p.phone,
                'is_dead': p.is_dead,
                'social_card1': p.social_card1,
                'social_card2': p.social_card2,
                'social_card3': p.social_card3,
                'social_card2_source': p.social_card2_source or '',
                'social_card3_source': p.social_card3_source or '',
                'poor_type': p.poor_type,
                'remark': p.remark,
                'disability': p.disability,
                'disability_type': p.disability_type,
                'dis_level': p.dis_level,
                'dibao': p.dibao,
                'tekun': p.tekun or '',
                'tekun_type': p.tekun_type or '',
                'jisheng': p.jisheng,
                'is_migrated': p.is_migrated,
                'land_area': p.land_area or '',
                'land_area_change_reason': p.land_area_change_reason or '',
                'land_area_change_time': p.land_area_change_time or '',
                'local_welfare_forest_area': p.local_welfare_forest_area or '',
                'local_welfare_forest_change_reason': p.local_welfare_forest_change_reason or '',
                'local_welfare_forest_change_time': p.local_welfare_forest_change_time or '',
                'national_welfare_forest_area': p.national_welfare_forest_area or '',
                'national_welfare_forest_change_reason': p.national_welfare_forest_change_reason or '',
                'national_welfare_forest_change_time': p.national_welfare_forest_change_time or '',
                'commercial_forest_area': p.commercial_forest_area or '',
                'commercial_forest_change_reason': p.commercial_forest_change_reason or '',
                'commercial_forest_change_time': p.commercial_forest_change_time or '',
                'updated_at': p.updated_at or '',
                'education': {
                    'school_name': edu.school_name,
                    'grade': GRADE_DISPLAY.get(edu.grade, edu.grade) if edu.grade else '',
                    'class_name': edu.class_name,
                    'guardian': edu.guardian,
                    'guardian_phone': edu.guardian_phone,
                    'is_left_behind': edu.is_left_behind,
                    'student_status': edu.student_status,
                    'enrollment_date': edu.enrollment_date,
                    'graduation_date': edu.graduation_date
                } if edu else None
            }
        })
    finally:
        session.close()


# 模块键 -> (展示名, 模型, 期间字段, 金额字段)
# 地力补贴的期间字段是 year、金额字段是 total_amount，其余 5 个模块统一为 period / amount
_SUBSIDY_MODULES = (
    ("dibao_payment", "低保", DibaoPayment, "period", "amount"),
    ("elderly_allowance", "高龄补贴", ElderlyAllowance, "period", "amount"),
    ("land_subsidy", "地力补贴", LandSubsidy, "year", "total_amount"),
    ("disability_care_payment", "残疾护理补贴", DisabilityCarePayment, "period", "amount"),
    ("pension_insurance", "养老保险", PensionInsurance, "period", "amount"),
    ("tekun_payment", "特困供养", TekunPayment, "period", "amount"),
)

_MAX_RECORDS = 300


def _to_amount(value) -> float:
    """把库里的金额字符串转成 float，非法值按 0 处理（不影响其它记录汇总）。"""
    try:
        return float(str(value or "").replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


@bp.route('/person/<person_id>/subsidies')
@require_auth
def api_person_subsidies(person_id):
    """按人聚合 6 个补贴模块的发放记录。

    person_id 可以是人员 id 或身份证号，与 /api/person/<person_id> 口径一致。
    """
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        id_card = (p.id_card or "").strip()
        if not id_card:
            return jsonify({
                'id_card': '',
                'person_name': p.name or '',
                'total_count': 0,
                'truncated': False,
                'by_module': [],
                'records': [],
            })

        records = []
        by_module = []
        for module, label, model, period_attr, amount_attr in _SUBSIDY_MODULES:
            rows = (
                session.query(model)
                .filter(getattr(model, "id_card") == id_card)
                .all()
            )
            total = 0.0
            for r in rows:
                period = getattr(r, period_attr, '') or ''
                amount = getattr(r, amount_attr, '') or ''
                total += _to_amount(amount)
                records.append({
                    'module': module,
                    'label': label,
                    'period': period,
                    'amount': amount,
                    'payment_status': getattr(r, 'payment_status', '') or '',
                    'fail_reason': getattr(r, 'fail_reason', '') or '',
                    'village': getattr(r, 'village', '') or '',
                    'town': getattr(r, 'town', '') or '',
                    'bank_account': getattr(r, 'bank_account', '') or '',
                })
            by_module.append({
                'module': module,
                'label': label,
                'count': len(rows),
                'total_amount': f"{total:.2f}" if total else '',
            })

        total_records = len(records)
        records.sort(key=lambda x: (x['period'] or ''), reverse=True)

        return jsonify({
            'id_card': id_card,
            'person_name': p.name or '',
            'total_count': total_records,
            'truncated': total_records > _MAX_RECORDS,
            'by_module': by_module,
            'records': records[:_MAX_RECORDS],
        })
    finally:
        session.close()
