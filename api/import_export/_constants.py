ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# Excel 文件 magic bytes
EXCEL_MAGIC_BYTES = {
    # XLSX 是 ZIP 格式
    b'\x50\x4B\x03\x04': 'xlsx',  # ZIP file signature (PK..)
    b'\x50\x4B\x05\x06': 'xlsx',  # Empty ZIP
    b'\x50\x4B\x07\x08': 'xlsx',  # Spanned ZIP
    # XLS 是 OLE 格式
    b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'xls',  # OLE compound document
}

# ── 支付类模板下载 ──
# 遵循"功能模块单独写、最后统一调用"：模板生成在 excel_payment_templates.py，API 统一调用

PAYMENT_TEMPLATE_MAP = {
    'land_subsidy': ('excel_payment_templates', 'generate_land_subsidy_template', '地力补贴导入模板.xlsx'),
    'pension_insurance': ('excel_payment_templates', 'generate_pension_insurance_template', '养老保险导入模板.xlsx'),
    'dibao_payment': ('excel_payment_templates', 'generate_dibao_payment_template', '低保发放导入模板.xlsx'),
    'tekun_payment': ('excel_payment_templates', 'generate_tekun_payment_template', '特困发放导入模板.xlsx'),
    'disability_care_payment': ('excel_payment_templates', 'generate_disability_care_payment_template', '残疾人护理补贴导入模板.xlsx'),
    'elderly_allowance': ('excel_payment_templates', 'generate_elderly_allowance_template', '高龄补贴导入模板.xlsx'),
}

# 短名别名：前端/旧链接使用短名时映射到完整类型
PAYMENT_TEMPLATE_MAP.update({
    'dibao': PAYMENT_TEMPLATE_MAP['dibao_payment'],
    'tekun': PAYMENT_TEMPLATE_MAP['tekun_payment'],
    'pension': PAYMENT_TEMPLATE_MAP['pension_insurance'],
    'elderly': PAYMENT_TEMPLATE_MAP['elderly_allowance'],
    'disability': PAYMENT_TEMPLATE_MAP['disability_care_payment'],
    'land': PAYMENT_TEMPLATE_MAP['land_subsidy'],
})
