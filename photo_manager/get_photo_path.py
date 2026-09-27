from config import PHOTOS_DIR
from utils import find_existing_photo, get_photo_base_name


def get_photo_path(photo_type: str, id_card: str, social1: str, social2: str, social3: str) -> str:
    base_name = get_photo_base_name(photo_type, id_card, social1, social2, social3)
    if not base_name:
        return ""
    return find_existing_photo(base_name, PHOTOS_DIR)
