import os
import shutil
from config import PHOTOS_DIR, PHOTO_EXTENSIONS
from utils import clean_filename, find_existing_photo, get_photo_base_name


def save_photo(source_path: str, photo_type: str, id_card: str, social1: str, social2: str, social3: str) -> bool:
    base_name = get_photo_base_name(photo_type, id_card, social1, social2, social3)
    if not base_name:
        return False
    cleaned = clean_filename(base_name)
    ext = os.path.splitext(source_path)[1].lower()
    if ext not in PHOTO_EXTENSIONS:
        return False
    dest = os.path.join(PHOTOS_DIR, cleaned + ext)
    old = find_existing_photo(base_name, PHOTOS_DIR)
    if old and old != dest and os.path.exists(old):
        os.remove(old)
    shutil.copy2(source_path, dest)
    return True
