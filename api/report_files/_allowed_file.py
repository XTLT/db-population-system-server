import os

ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.et'}


def _allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS
