import os
import secrets
from flask import request, jsonify

from database import add_operation_log
from utils.security import require_auth
from config import BASE_DIR, MAX_EXCEL_UPLOAD_SIZE
from . import bp
from ._constants import ALLOWED_EXTENSIONS
from ._validate import validate_excel_content


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
