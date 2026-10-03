# excel_payment_templates 包 — 向后兼容 shim
from ._write_template import _write_template
from ._constants import (
    LAND_SUBSIDY_COLUMNS,
    PENSION_INSURANCE_COLUMNS,
    DIBAO_PAYMENT_COLUMNS,
    TEKUN_PAYMENT_COLUMNS,
    DISABILITY_CARE_PAYMENT_COLUMNS,
    ELDERLY_ALLOWANCE_COLUMNS,
)
from .generate_land_subsidy_template import generate_land_subsidy_template
from .generate_pension_insurance_template import generate_pension_insurance_template
from .generate_dibao_payment_template import generate_dibao_payment_template
from .generate_tekun_payment_template import generate_tekun_payment_template
from .generate_disability_care_payment_template import generate_disability_care_payment_template
from .generate_elderly_allowance_template import generate_elderly_allowance_template

__all__ = [
    '_write_template',
    'LAND_SUBSIDY_COLUMNS',
    'PENSION_INSURANCE_COLUMNS',
    'DIBAO_PAYMENT_COLUMNS',
    'TEKUN_PAYMENT_COLUMNS',
    'DISABILITY_CARE_PAYMENT_COLUMNS',
    'ELDERLY_ALLOWANCE_COLUMNS',
    'generate_land_subsidy_template',
    'generate_pension_insurance_template',
    'generate_dibao_payment_template',
    'generate_tekun_payment_template',
    'generate_disability_care_payment_template',
    'generate_elderly_allowance_template',
]
