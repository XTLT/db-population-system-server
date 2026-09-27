import os
import shutil


def export_photo(source_path: str, dest_path: str) -> bool:
    if os.path.exists(source_path):
        shutil.copy2(source_path, dest_path)
        return True
    return False
