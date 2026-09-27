from ._write_template import _write_template
from ._constants import DIBAO_PAYMENT_COLUMNS


def generate_dibao_payment_template(path):
    _write_template(path, "低保发放", DIBAO_PAYMENT_COLUMNS)
