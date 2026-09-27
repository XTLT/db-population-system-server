import os


def find_existing_photo(base_name: str, photos_dir: str) -> str:
    """查找已存在的照片文件"""
    if not os.path.isdir(photos_dir):
        return ""

    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    for ext in extensions:
        photo_path = os.path.join(photos_dir, base_name + ext)
        if os.path.exists(photo_path):
            return photo_path
    return ""
