import os
import secrets
from datetime import datetime
from flask import request, jsonify, send_file

from utils.security import require_auth
from database import get_session, LandSubsidy, Person, add_operation_log
from config import BASE_DIR
from . import bp


@bp.route('/land_subsidy/export')
@require_auth
def export_land_subsidy():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    year = request.args.get('year', '')

    session = get_session()
    try:
        query = session.query(LandSubsidy)
        if year:
            query = query.filter(LandSubsidy.year == year)

        subsidies = query.order_by(LandSubsidy.year.desc()).all()

        if not subsidies:
            return jsonify({'error': '没有数据可导出'}), 404

        person_map = {}
        for p in session.query(Person).all():
            if p.id_card:
                person_map[p.id_card] = p

        def _card_of(id_card):
            p = person_map.get(id_card)
            if not p:
                return ''
            for c in (p.social_card1, p.social_card2, p.social_card3):
                if c and c != '无':
                    return c
            return ''

        import pandas as pd
        # 列名与模板（excel_payment_templates/_constants.py LAND_SUBSIDY_COLUMNS）保持一致，
        # 导出文件可被导入器直接回环导入（导入器同时兼容长名与历史短名）。
        data = [{
            '补贴年度': s.year,
            '户主姓名': s.name,
            '身份证号': s.id_card,
            '电话号码': s.phone,
            '银行账号': '',
            '金融机构': s.bank_name,
            '发放金额': s.total_amount,
            '上账时间': s.land_time,
            '耕地面积': s.certified_area,
            '耕地标准': s.base_standard,
            '油菜面积': s.rape_area,
            '油菜标准': '',
            '油菜金额': s.rape_amount,
            '卡号': _card_of(s.id_card),
            '导入时间': s.import_time or s.created_at
        } for s in subsidies]

        df = pd.DataFrame(data)
        tmp_path = os.path.join(BASE_DIR, f'_tmp_land_exp_{secrets.token_hex(4)}.xlsx')
        df.to_excel(tmp_path, index=False, engine='openpyxl')

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导出土地补贴",
            f"导出{len(subsidies)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return send_file(tmp_path, as_attachment=True,
                        download_name=f'土地补贴_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
