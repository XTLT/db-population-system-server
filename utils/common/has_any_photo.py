import os


def has_any_photo(id_card: str, social1: str, social2: str, social3: str, photos_dir: str) -> bool:
    """检查是否有任何照片"""
    from config import PHOTO_EXTENSIONS

    if not os.path.isdir(photos_dir):
        return False

    base_name = id_card
    for ext in PHOTO_EXTENSIONS:
        # 身份证照片
        if os.path.exists(os.path.join(photos_dir, f"{base_name}_身份证{ext}")):
            return True
        # 社保卡照片
        if social1 and os.path.exists(os.path.join(photos_dir, f"{base_name}_社保卡1{ext}")):
            return True
        if social2 and os.path.exists(os.path.join(photos_dir, f"{base_name}_社保卡2{ext}")):
            return True
        if social3 and os.path.exists(os.path.join(photos_dir, f"{base_name}_社保卡3{ext}")):
            return True
    return False
