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
                'land_area': s.land_area,
                'subsidy_amount': s.subsidy_amount,
                'created_at': s.created_at
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
        total_amount = session.query(func.sum(LandSubsidy.subsidy_amount)).scalar() or 0
        
        by_year = session.query(
            LandSubsidy.year,
            func.count(LandSubsidy.id),
            func.sum(LandSubsidy.subsidy_amount)
        ).group_by(LandSubsidy.year).order_by(LandSubsidy.year.desc()).all()
        
        return jsonify({
            'total_count': total_count,
            'total_amount': float(total_amount),
            'by_year': [{
                'year': y[0],
                'count': y[1],
                'amount': float(y[2] or 0)
            } for y in by_year]
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
            '土地面积': s.land_area,
            '补贴金额': s.subsidy_amount,
            '创建时间': s.created_at
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
