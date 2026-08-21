import os
import secrets
from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import config
from config.database import init_db


def create_app():
    app = Flask(__name__)
    
    env_key = os.getenv('SECRET_KEY')
    if env_key:
        app.config['SECRET_KEY'] = env_key
    else:
        app.config['SECRET_KEY'] = secrets.token_hex(32)
    
    app.config['DEBUG'] = config.debug
    
    allowed_origins = config.get('domains.allowed_origins', ['*'])
    CORS(app, origins=allowed_origins)
    
    from api.v1 import auth, persons, students
    app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
    app.register_blueprint(persons.bp, url_prefix='/api/v1/persons')
    app.register_blueprint(students.bp, url_prefix='/api/v1/students')
    
    @app.route('/api/health')
    def health_check():
        from datetime import datetime
        return jsonify({
            'status': 'ok',
            'version': config.version,
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/domains/status')
    def domain_status():
        from config.domains import domain_manager
        report = domain_manager.get_domain_status_report()
        return jsonify({
            'report': report
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': '服务器内部错误'}), 500
    
    return app


app = create_app()


if __name__ == '__main__':
    init_db()
    
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.debug
    )
