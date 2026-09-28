from ._write_template import _write_template
from ._constants import DISABILITY_CARE_PAYMENT_COLUMNS


def generate_disability_care_payment_template(path):
    _write_template(path, "残疾人护理补贴发放", DISABILITY_CARE_PAYMENT_COLUMNS)
