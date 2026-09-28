from ._write_template import _write_template
from ._constants import ELDERLY_ALLOWANCE_COLUMNS


def generate_elderly_allowance_template(path):
    _write_template(path, "高龄补贴发放", ELDERLY_ALLOWANCE_COLUMNS)
