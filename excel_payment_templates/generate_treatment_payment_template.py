from ._write_template import _write_template
from ._constants import TREATMENT_PAYMENT_COLUMNS


def generate_treatment_payment_template(path):
    _write_template(path, "待遇发放", TREATMENT_PAYMENT_COLUMNS)
