from flask import Blueprint

bp = Blueprint('dibao_payment', __name__)

from . import import_dibao_payment  # noqa: E402,F401
from . import list_dibao_payments  # noqa: E402,F401
from . import get_dibao_payment_years  # noqa: E402,F401
from . import get_dibao_payment_periods  # noqa: E402,F401
from . import get_dibao_payment_statistics  # noqa: E402,F401
from . import delete_dibao_payment  # noqa: E402,F401
from . import export_dibao_payment  # noqa: E402,F401
