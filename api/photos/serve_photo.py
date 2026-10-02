import os
from flask import jsonify

from utils.security import require_auth
from . import bp, logger, PHOTO_UPLOAD_DIR


@bp.route('/photo/<filename>')
@require_auth
def api_serve_photo(filename):
    """提供照片文件访问（需要认证）"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': '无效的文件名'}), 400
        
        # 检查文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 安全检查：只允许访问 Photos 目录下的文件
        file_path = os.path.join(PHOTO_UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': '照片不存在'}), 404
        
        # 检查文件是否在允许的目录内
        real_path = os.path.realpath(file_path)
        if not real_path.startswith(os.path.realpath(PHOTO_UPLOAD_DIR)):
            return jsonify({'error': '无权访问'}), 403
        
        from flask import send_file
        return send_file(file_path)
    except Exception as e:
        logger.error(f"照片访问错误: {e}")
        return jsonify({'error': '服务器错误'}), 500
