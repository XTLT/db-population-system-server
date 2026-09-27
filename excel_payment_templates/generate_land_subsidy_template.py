from ._write_template import _write_template
from ._constants import LAND_SUBSIDY_COLUMNS


def generate_land_subsidy_template(path):
    _write_template(path, "地力补贴", LAND_SUBSIDY_COLUMNS)
