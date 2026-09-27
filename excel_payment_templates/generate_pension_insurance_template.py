from ._write_template import _write_template
from ._constants import PENSION_INSURANCE_COLUMNS


def generate_pension_insurance_template(path):
    _write_template(path, "养老保险", PENSION_INSURANCE_COLUMNS)
