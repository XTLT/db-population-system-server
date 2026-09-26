import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from database import get_session, add_operation_log
from utils.security import require_auth
from config import BASE_DIR, EXCEL_TEMPLATE_COLUMNS, MAX_EXCEL_UPLOAD_SIZE

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# Excel 文件 magic bytes
EXCEL_MAGIC_BYTES = {
    # XLSX 是 ZIP 格式
    b'\x50\x4B\x03\x04': 'xlsx',  # ZIP file signature (PK..)
    b'\x50\x4B\x05\x06': 'xlsx',  # Empty ZIP
    b'\x50\x4B\x07\x08': 'xlsx',  # Spanned ZIP
    # XLS 是 OLE 格式
    b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'xls',  # OLE compound document
}


def validate_excel_content(file_obj):
    """验证 Excel 文件内容（通过 magic bytes）
    
    Returns:
        (is_valid, file_type) 或 (False, None)
    """
    try:
        file_obj.seek(0)
        header = file_obj.read(8)
        file_obj.seek(0)
        
        for magic, file_type in EXCEL_MAGIC_BYTES.items():
            if header.startswith(magic):
                return True, file_type
        
        return False, None
    except Exception:
        return False, None


bp = Blueprint('import_export', __name__)


@bp.route('/import/excel', methods=['POST'])
@require_auth
def api_import_excel():
    """Excel 导入
    
    支持两种导入模式：
    - incremental: 增量导入，只新增不覆盖
    - full: 全量导入，清空后重新导入
    """
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足，仅管理员可导入'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400
    
    # 检查文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'不支持的文件格式，仅支持：{", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # 验证文件内容（magic bytes）
    is_valid, file_type = validate_excel_content(file)
    if not is_valid:
        return jsonify({'error': '文件内容验证失败：不是有效的 Excel 文件'}), 400
    
    # 检查扩展名与实际内容是否匹配
    if file_type == 'xlsx' and ext != '.xlsx':
        return jsonify({'error': '文件扩展名与内容不匹配'}), 400
    if file_type == 'xls' and ext != '.xls':
        return jsonify({'error': '文件扩展名与内容不匹配'}), 400
    
    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_EXCEL_UPLOAD_SIZE:
        return jsonify({'error': f'文件大小超过限制（最大 {MAX_EXCEL_UPLOAD_SIZE // (1024*1024)}MB）'}), 400
    
    mode = request.form.get('mode', 'incremental')
    
    # 验证导入模式
    if mode not in ['incremental', 'full']:
        return jsonify({'error': '无效的导入模式，仅支持 incremental 或 full'}), 400
    
    tmp_path = os.path.join(BASE_DIR, f'_tmp_import_{secrets.token_hex(4)}.xlsx')
    
    try:
        file.save(tmp_path)
        from excel_importer import import_excel_full, import_excel_incremental
        
        if mode == 'full':
            result = import_excel_full(tmp_path)
        else:
            result = import_excel_incremental(tmp_path)
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入Excel",
            f"模式:{mode} 成功:{result.get('imported',0)}",
            request.remote_addr,
            "Web"
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@bp.route('/export/excel', methods=['POST'])
@require_auth
def export_excel():
    """导出人员数据到 Excel
    
    权限要求: admin 或 user
    需要二次密码验证
    
    Request Body:
        password: 用户密码
        filters: 筛选条件（可选）
    """
    from database import User
    from utils.security import verify_password
    
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json() or {}
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': '导出敏感数据需要验证密码'}), 401
    
    user_id = request.current_user['id']
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        is_valid, _ = verify_password(password, user.password_hash)
        if not is_valid:
            return jsonify({'error': '密码错误'}), 401
    finally:
        session.close()
    
    try:
        from excel_importer import export_excel as do_export
        tmp_path = os.path.join(BASE_DIR, f'_tmp_export_{secrets.token_hex(4)}.xlsx')
        
        if do_export(tmp_path):
            add_operation_log(
                request.current_user['id'],
                request.current_user['username'],
                "导出Excel",
                "导出人员数据",
                request.remote_addr,
                "Web"
            )
            return send_file(tmp_path, as_attachment=True,
                           download_name=f'人口信息_{datetime.now().strftime("%Y%m%d")}.xlsx')
        return jsonify({'error': '没有数据可导出'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/template/excel')
@require_auth
def download_excel_template():
    """下载人员信息导入模板
    
    Returns:
        Excel 模板文件
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    
    tmp_path = os.path.join(BASE_DIR, f'_tmp_tpl_{secrets.token_hex(4)}.xlsx')
    
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "人口信息"
        
        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        # 写入表头
        for col_idx, col_name in enumerate(EXCEL_TEMPLATE_COLUMNS, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # 设置列宽
        for col_idx in range(1, len(EXCEL_TEMPLATE_COLUMNS) + 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 15
        
        wb.save(tmp_path)
        return send_file(tmp_path, as_attachment=True, 
                        download_name='人口信息导入模板.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ── 支付类模板下载 ──
# 遵循"功能模块单独写、最后统一调用"：模板生成在 excel_payment_templates.py，API 统一调用

PAYMENT_TEMPLATE_MAP = {
    'land_subsidy': ('excel_payment_templates', 'generate_land_subsidy_template', '地力补贴导入模板.xlsx'),
    'treatment_payment': ('excel_payment_templates', 'generate_treatment_payment_template', '待遇发放导入模板.xlsx'),
    'pension_insurance': ('excel_payment_templates', 'generate_pension_insurance_template', '养老保险导入模板.xlsx'),
    'dibao_payment': ('excel_payment_templates', 'generate_dibao_payment_template', '低保发放导入模板.xlsx'),
    'tekun_payment': ('excel_payment_templates', 'generate_tekun_payment_template', '特困发放导入模板.xlsx'),
}


@bp.route('/template/payment/<payment_type>')
@require_auth
def download_payment_template(payment_type):
    """下载支付类导入模板

    Args:
        payment_type: land_subsidy | treatment_payment | pension_insurance | dibao_payment | tekun_payment

    Returns:
        Excel 模板文件
    """
    config = PAYMENT_TEMPLATE_MAP.get(payment_type)
    if not config:
        return jsonify({'error': f'未知的模板类型: {payment_type}'}), 400

    module_name, func_name, download_name = config
    tmp_path = os.path.join(BASE_DIR, f'_tmp_tpl_{payment_type}_{secrets.token_hex(4)}.xlsx')

    try:
        import importlib
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        func(tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/template/student')
@require_auth
def download_student_template():
    """下载学生信息导入模板
    
    Returns:
        Excel 模板文件
    """
    tmp_path = os.path.join(BASE_DIR, f'_tmp_stu_tpl_{secrets.token_hex(4)}.xlsx')
    
    try:
        from student_importer import export_student_education_template
        export_student_education_template(tmp_path)
        return send_file(tmp_path, as_attachment=True, 
                        download_name='学生就读信息导入模板.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/template/forest')
@require_auth
def download_forest_template():
    """下载林地面积导入模板

    Returns:
        Excel 模板文件
    """
    tmp_path = os.path.join(BASE_DIR, f'_tmp_forest_tpl_{secrets.token_hex(4)}.xlsx')

    try:
        from excel_forest_template import generate_forest_template
        generate_forest_template(tmp_path)
        return send_file(tmp_path, as_attachment=True,
                        download_name='林地面积导入模板.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
