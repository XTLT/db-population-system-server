import os
from config import PHOTOS_DIR
from utils import find_existing_photo, get_photo_base_name


def delete_photo(photo_type: str, id_card: str, social1: str, social2: str, social3: str) -> bool:
    base_name = get_photo_base_name(photo_type, id_card, social1, social2, social3)
    if not base_name:
        return False
    path = find_existing_photo(base_name, PHOTOS_DIR)
    if path and os.path.exists(path):
        os.remove(path)
        return True
    return False
