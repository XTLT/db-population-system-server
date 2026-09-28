from flask import Blueprint

bp = Blueprint('elderly_allowance', __name__)

from . import import_elderly_allowance  # noqa: E402,F401
from . import list_elderly_allowances  # noqa: E402,F401
from . import get_elderly_allowance_years  # noqa: E402,F401
from . import get_elderly_allowance_periods  # noqa: E402,F401
from . import get_elderly_allowance_statistics  # noqa: E402,F401
from . import delete_elderly_allowance  # noqa: E402,F401
from . import export_elderly_allowance  # noqa: E402,F401
