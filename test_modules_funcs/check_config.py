"""检查关键配置常量能否正常读取。"""


def check_config():
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
