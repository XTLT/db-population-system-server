import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import func

from utils.security import require_auth
from utils.response import safe_error
from utils import escape_like, validate_year, validate_id_card
from database import get_session, LandSubsidy, Person, add_operation_log
from config import BASE_DIR

bp = Blueprint('land_subsidy', __name__)


@bp.route('/land_subsidy/import', methods=['POST'])
@require_auth
def import_land_subsidy():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    subsidy_year = request.form.get('subsidy_year', '')
    
    if subsidy_year:
        valid, msg = validate_year(subsidy_year)
        if not valid:
            return jsonify({'error': f'补贴年份: {msg}'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400
    
    tmp_path = os.path.join(BASE_DIR, f'_tmp_land_{secrets.token_hex(4)}.xlsx')
    
    try:
        file.save(tmp_path)
        from excel_importer import import_land_subsidy_excel
        result = import_land_subsidy_excel(tmp_path, subsidy_year)
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入土地补贴",
            f"导入{result.get('imported', 0)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@bp.route('/land_subsidy')
@require_auth
def list_land_subsidies():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    year = request.args.get('year', '')
    id_card = request.args.get('id_card', '')
    
    if year:
        valid, msg = validate_year(year)
        if not valid:
            return jsonify({'error': f'年份: {msg}'}), 400
    
    session = get_session()
    try:
        query = session.query(LandSubsidy)
        
        if year:
            query = query.filter(LandSubsidy.year == year)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(LandSubsidy.id_card.like(f'%{safe_id_card}%', escape='\\'))
        
        subsidies = query.order_by(LandSubsidy.year.desc()).limit(500).all()
        
        return jsonify({
            'subsidies': [{
                'id': s.id,
                'person_id': s.person_id,
                'id_card': s.id_card,
                'name': s.name,
                'year': s.year,
                'certified_area': s.certified_area,
                'subsidy_area': s.subsidy_area,
                'base_standard': s.base_standard,
                'rape_area': s.rape_area,
                'rape_amount': s.rape_amount,
                'total_amount': s.total_amount,
                'import_time': s.import_time or s.created_at
            } for s in subsidies]
        })
    finally:
        session.close()


@bp.route('/land_subsidy/years')
@require_auth
def get_subsidy_years():
    session = get_session()
    try:
        years = session.query(LandSubsidy.year).distinct().order_by(LandSubsidy.year.desc()).all()
        return jsonify({
            'years': [y[0] for y in years if y[0]]
        })
    finally:
        session.close()


@bp.route('/land_subsidy/statistics')
@require_auth
def subsidy_statistics():
    session = get_session()
    try:
        total_count = session.query(LandSubsidy).count()
        # subsidy_amount 是字符串，需要在 Python 中计算
        subsidies = session.query(LandSubsidy).all()
        total_amount = 0.0
        for s in subsidies:
            try:
                total_amount += float(s.subsidy_amount) if s.subsidy_amount else 0
            except (ValueError, TypeError):
                pass
        
        by_year = {}
        for s in subsidies:
            year = s.year or "未知"
            if year not in by_year:
                by_year[year] = {'count': 0, 'amount': 0.0}
            by_year[year]['count'] += 1
            try:
                by_year[year]['amount'] += float(s.subsidy_amount) if s.subsidy_amount else 0
            except (ValueError, TypeError):
                pass
        
        return jsonify({
            'total_count': total_count,
            'total_amount': total_amount,
            'by_year': [{
                'year': y,
                'count': by_year[y]['count'],
                'amount': by_year[y]['amount']
            } for y in sorted(by_year.keys(), reverse=True)]
        })
    finally:
        session.close()


@bp.route('/land_subsidy/<subsidy_id>', methods=['DELETE'])
@require_auth
def delete_subsidy(subsidy_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        subsidy = session.query(LandSubsidy).filter(LandSubsidy.id == subsidy_id).first()
        if not subsidy:
            return jsonify({'error': '记录不存在'}), 404
        
        session.delete(subsidy)
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除补贴记录",
            subsidy_id,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()


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
        
        import pandas as pd
        data = [{
            '身份证号': s.id_card,
            '姓名': s.name,
            '年份': s.year,
            '确权面积': s.certified_area,
            '补贴面积': s.subsidy_area,
            '基础标准': s.base_standard,
            '油菜面积': s.rape_area,
            '油菜金额': s.rape_amount,
            '补贴总金额': s.total_amount,
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
