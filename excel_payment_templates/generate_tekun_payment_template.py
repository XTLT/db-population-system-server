from ._write_template import _write_template
from ._constants import TEKUN_PAYMENT_COLUMNS


def generate_tekun_payment_template(path):
    _write_template(path, "特困发放", TEKUN_PAYMENT_COLUMNS)
