#!/usr/bin/env python3
"""
模块验证脚本 - 检查所有模块是否正常
"""
import sys
import os

# 添加 server 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_syntax():
    """检查语法（递归编译 server/ 下所有 .py，排除 legacy 单体与 venv/备份）"""
    print("=== 语法检查 ===")
    import py_compile
    server_dir = os.path.dirname(os.path.abspath(__file__))
    exclude_dirs = {'venv', '__pycache__', 'config_test_bak'}
    exclude_files = {'web_app.py'}  # 旧单体，已被 api/ + app_modular.py 取代
    ok = fail = 0
    for root, dirs, files in os.walk(server_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for name in files:
            if not name.endswith('.py') or name in exclude_files:
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, server_dir)
            try:
                py_compile.compile(path, doraise=True)
                ok += 1
            except py_compile.PyCompileError as e:
                print(f"  ✗ {rel}: {e}")
                fail += 1
    print(f"  编译完成: OK={ok} FAIL={fail}")
    return fail == 0


def check_structure():
    """检查模块结构"""
    print("\n=== 结构检查 ===")
    
    # 检查 utils
    from utils.security import hash_password, verify_password, require_auth, create_token
    print("  ✓ utils/security.py - hash_password, verify_password, require_auth, create_token")
    
    from utils.response import safe_error, get_json_data
    print("  ✓ utils/response.py - safe_error, get_json_data")
    
    # 检查 API 模块
    from api import (
        auth_bp, users_bp, persons_bp, students_bp,
        photos_bp, statistics_bp, import_export_bp,
        backup_bp, logs_bp, notifications_bp, reports_bp
    )
    print("  ✓ 所有 Blueprint 导入成功")
    
    # 列出所有蓝图
    print("\n=== Blueprint 列表 ===")
    for bp in [auth_bp, users_bp, persons_bp, students_bp, photos_bp, 
               statistics_bp, import_export_bp, backup_bp, logs_bp, 
               notifications_bp, reports_bp]:
        print(f"  - {bp.name}")
    
    return True


def check_config():
    """检查配置常量"""
    print("\n=== 配置检查 ===")
    from config import (
        BASE_DIR, DATA_DIR, DB_PATH, PHOTOS_DIR, BACKUP_DIR,
        TOKEN_EXPIRY_HOURS, LOGIN_LOCK_MINUTES,
        GRADE_DISPLAY, PHOTO_EXTENSIONS
    )
    print(f"  ✓ BASE_DIR: {BASE_DIR}")
    print(f"  ✓ DATA_DIR: {DATA_DIR}")
    print(f"  ✓ TOKEN_EXPIRY_HOURS: {TOKEN_EXPIRY_HOURS}")
    print(f"  ✓ GRADE_DISPLAY: {len(GRADE_DISPLAY)} 项")
    print(f"  ✓ PHOTO_EXTENSIONS: {PHOTO_EXTENSIONS}")
    return True


def main():
    print("=" * 50)
    print("模块验证脚本")
    print("=" * 50)
    
    # 语法检查
    if not check_syntax():
        print("\n❌ 语法检查失败")
        return 1
    
    # 结构检查
    try:
        if not check_structure():
            print("\n❌ 结构检查失败")
            return 1
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1
    
    # 配置检查
    try:
        if not check_config():
            print("\n❌ 配置检查失败")
            return 1
    except ImportError as e:
        print(f"\n❌ 配置导入失败: {e}")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ 所有模块检查通过")
    print("=" * 50)
    return 0


if __name__ == '__main__':
    sys.exit(main())
