import os


def validate_photo_filename(filename: str) -> tuple:
    """验证照片文件名格式

    Returns:
        (is_valid, id_card, photo_type, extension)
    """
    if not filename:
        return False, None, None, None

    # 支持的扩展名
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']

    # 分离扩展名
    name, ext = os.path.splitext(filename.lower())
    if ext not in valid_extensions:
        return False, None, None, None

    # 解析文件名格式: {身份证号}_{照片类型}
    parts = name.split('_')
    if len(parts) != 2:
        return False, None, None, None

    id_card, photo_type = parts

    # 验证身份证号格式
    if not (id_card[:-1].isdigit() and id_card[-1] in '0123456789xX') or len(id_card) != 18:
        return False, None, None, None

    return True, id_card, photo_type, ext
