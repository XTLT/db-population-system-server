from .import_treatment_payment import import_treatment_payment


def import_treatment_payment_excel(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入待遇发放数据 - API 别名"""
    return import_treatment_payment(file_path, progress_callback, period=period)
