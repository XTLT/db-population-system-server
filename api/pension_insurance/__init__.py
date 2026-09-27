from flask import Blueprint

bp = Blueprint('pension_insurance', __name__)

from . import import_pension_insurance  # noqa: E402,F401
from . import list_pension_insurance  # noqa: E402,F401
from . import get_pension_insurance_years  # noqa: E402,F401
from . import get_pension_insurance_periods  # noqa: E402,F401
from . import get_pension_insurance_statistics  # noqa: E402,F401
from . import delete_pension_insurance  # noqa: E402,F401
from . import export_pension_insurance  # noqa: E402,F401
