import os
from config import PHOTOS_DIR
from utils import find_existing_photo


def get_photo_status(id_card: str, social1: str, social2: str, social3: str) -> str:
    for card in [id_card, social1, social2, social3]:
        path = find_existing_photo(card, PHOTOS_DIR)
        if path:
            ext = os.path.splitext(path)[1].upper()
            return f"已有照片 ({ext[1:]})"
    return "暂无照片"
