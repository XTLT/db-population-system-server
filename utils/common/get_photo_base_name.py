def get_photo_base_name(photo_type: str, id_card: str, social1: str, social2: str, social3: str) -> str:
    """获取照片基础文件名"""
    if photo_type == "身份证":
        return f"{id_card}_身份证"
    elif photo_type == "社保卡1":
        return f"{id_card}_社保卡1"
    elif photo_type == "社保卡2":
        return f"{id_card}_社保卡2"
    elif photo_type == "社保卡3":
        return f"{id_card}_社保卡3"
    return ""
