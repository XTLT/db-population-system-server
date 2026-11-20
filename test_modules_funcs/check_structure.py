"""检查工具模块与所有 Blueprint 能否正常导入。"""


def check_structure():
    print("\n=== 结构检查 ===")

    from utils.security import hash_password, verify_password, require_auth, create_token
    print("  ✓ utils/security.py - hash_password, verify_password, require_auth, create_token")

    from utils.response import safe_error, get_json_data
    print("  ✓ utils/response.py - safe_error, get_json_data")

    from api import (
        auth_bp, users_bp, persons_bp, students_bp,
        photos_bp, statistics_bp, import_export_bp,
        backup_bp, logs_bp, notifications_bp, reports_bp
    )
    print("  ✓ 所有 Blueprint 导入成功")

    print("\n=== Blueprint 列表 ===")
    for bp in [auth_bp, users_bp, persons_bp, students_bp, photos_bp,
               statistics_bp, import_export_bp, backup_bp, logs_bp,
               notifications_bp, reports_bp]:
        print(f"  - {bp.name}")

    return True
