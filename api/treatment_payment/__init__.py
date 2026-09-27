from flask import Blueprint

bp = Blueprint('treatment_payment', __name__)

from . import import_treatment_payment  # noqa: E402,F401
from . import list_treatment_payments  # noqa: E402,F401
from . import get_treatment_payment_years  # noqa: E402,F401
from . import get_treatment_payment_periods  # noqa: E402,F401
from . import get_treatment_payment_statistics  # noqa: E402,F401
from . import delete_treatment_payment  # noqa: E402,F401
from . import export_treatment_payment  # noqa: E402,F401
