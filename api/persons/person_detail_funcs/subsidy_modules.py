"""人员详情相关接口共用的补贴模块表与截断上限。"""

from database import (
    DibaoPayment, DisabilityCarePayment, ElderlyAllowance,
    LandSubsidy, PensionInsurance, TekunPayment,
)

# 模块键 -> (展示名, 模型, 期间字段, 金额字段)
# 地力补贴的期间字段是 year、金额字段是 total_amount，其余 5 个模块统一为 period / amount
SUBSIDY_MODULES = (
    ("dibao_payment", "低保", DibaoPayment, "period", "amount"),
    ("elderly_allowance", "高龄补贴", ElderlyAllowance, "period", "amount"),
    ("land_subsidy", "地力补贴", LandSubsidy, "year", "total_amount"),
    ("disability_care_payment", "残疾护理补贴", DisabilityCarePayment, "period", "amount"),
    ("pension_insurance", "养老保险", PensionInsurance, "period", "amount"),
    ("tekun_payment", "特困供养", TekunPayment, "period", "amount"),
)

MAX_RECORDS = 300
DATA_HEALTH_MAX_ITEMS = 200
