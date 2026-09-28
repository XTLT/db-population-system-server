from flask import Blueprint

bp = Blueprint('disability_care_payment', __name__)

from . import import_disability_care_payment  # noqa: E402,F401
from . import list_disability_care_payments  # noqa: E402,F401
from . import get_disability_care_payment_years  # noqa: E402,F401
from . import get_disability_care_payment_periods  # noqa: E402,F401
from . import get_disability_care_payment_statistics  # noqa: E402,F401
from . import delete_disability_care_payment  # noqa: E402,F401
from . import export_disability_care_payment  # noqa: E402,F401
