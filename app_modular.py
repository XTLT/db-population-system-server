import os
import sys
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

logger = logging.getLogger('population_system')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BASE_DIR

if getattr(sys, 'frozen', False):
    _MEIPASS = sys._MEIPASS
    _search_dirs = [
        os.path.join(_MEIPASS, 'server', 'web_static'),
        os.path.join(_MEIPASS, 'web_static'),
    ]
else:
    _search_dirs = [os.path.join(BASE_DIR, 'web_static')]

STATIC_DIR = None
for _d in _search_dirs:
    if os.path.isdir(_d):
        STATIC_DIR = _d
        break
if STATIC_DIR is None:
    STATIC_DIR = _search_dirs[0]


def create_app():
    import secrets
    app = Flask(__name__)
    
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        app.secret_key = env_key
    else:
        app.secret_key = secrets.token_hex(32)
    
    # 文件上传大小限制（16MB）
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
    
    from api import (
        auth_bp, users_bp, persons_bp, students_bp,
        photos_bp, statistics_bp, import_export_bp,
        backup_bp, logs_bp, notifications_bp, reports_bp,
        land_subsidy_bp, treatment_payment_bp, pension_insurance_bp,
        dibao_payment_bp, tekun_payment_bp,
        update_bp, report_files_bp
    )
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(persons_bp, url_prefix='/api')
    app.register_blueprint(students_bp, url_prefix='/api')
    app.register_blueprint(photos_bp, url_prefix='/api')
    app.register_blueprint(statistics_bp, url_prefix='/api')
    app.register_blueprint(import_export_bp, url_prefix='/api')
    app.register_blueprint(backup_bp, url_prefix='/api/backup')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(report_files_bp, url_prefix='/api/reports')
    app.register_blueprint(land_subsidy_bp, url_prefix='/api')
    app.register_blueprint(treatment_payment_bp, url_prefix='/api')
    app.register_blueprint(pension_insurance_bp, url_prefix='/api')
    app.register_blueprint(dibao_payment_bp, url_prefix='/api')
    app.register_blueprint(tekun_payment_bp, url_prefix='/api')
    app.register_blueprint(update_bp, url_prefix='/api/update')

    @app.route('/api/health')
    def health_check():
        return jsonify({'healthy': True})

    @app.route('/')
    def index():
        return send_from_directory(STATIC_DIR, 'index.html')
    
    @app.route('/style.css')
    def style():
        return send_from_directory(STATIC_DIR, 'style.css')
    
    @app.route('/app.js')
    def script():
        return send_from_directory(STATIC_DIR, 'app.js')

    @app.route('/js/<path:filename>')
    def js_files(filename):
        return send_from_directory(os.path.join(STATIC_DIR, 'js'), filename)

    @app.route('/favicon.ico')
    def favicon():
        return ('', 204)
    
    @app.after_request
    def add_security_headers(response):
        response.headers.pop('Server', None)
        response.headers.pop('ETag', None)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
        
        from ssl_utils import get_cert_paths
        cert_file, key_file = get_cert_paths()
        if cert_file and os.path.exists(cert_file):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': '资源不存在'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        app.logger.error("500 Internal Error: %s\n%s", error, traceback.format_exc())
        return {'error': '服务器内部错误'}, 500
    
    from config import ensure_dirs
    ensure_dirs()

    from database import init_db
    init_db()

    from utils.security import cleanup_expired_tokens
    cleanup_expired_tokens()

    from api.auth import _ensure_default_admin
    _ensure_default_admin()

    return app


app = create_app()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    from ssl_utils import generate_self_signed_cert
    cert_file, key_file = generate_self_signed_cert()
    
    if cert_file and key_file:
        logger.info(f"人口通启动 - HTTPS 已启用，端口: {port}")
        ssl_context = (cert_file, key_file)
    else:
        logger.info(f"人口通启动 - HTTP 模式，端口: {port}")
        ssl_context = None
    
    app.run(
        host='::',
        port=port,
        threaded=True,
        debug=os.environ.get('FLASK_DEBUG', '0') == '1',
        ssl_context=ssl_context
    )
