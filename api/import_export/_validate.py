from ._constants import EXCEL_MAGIC_BYTES


def validate_excel_content(file_obj):
    """验证 Excel 文件内容（通过 magic bytes）
    
    Returns:
        (is_valid, file_type) 或 (False, None)
    """
    try:
        file_obj.seek(0)
        header = file_obj.read(8)
        file_obj.seek(0)
        
        for magic, file_type in EXCEL_MAGIC_BYTES.items():
            if header.startswith(magic):
                return True, file_type
        
        return False, None
    except Exception:
        return False, None
