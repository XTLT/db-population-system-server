from flask import Blueprint

bp = Blueprint('tekun_payment', __name__)

from . import import_tekun_payment  # noqa: E402,F401
from . import list_tekun_payments  # noqa: E402,F401
from . import get_tekun_payment_years  # noqa: E402,F401
from . import get_tekun_payment_periods  # noqa: E402,F401
from . import get_tekun_payment_statistics  # noqa: E402,F401
from . import delete_tekun_payment  # noqa: E402,F401
from . import export_tekun_payment  # noqa: E402,F401
