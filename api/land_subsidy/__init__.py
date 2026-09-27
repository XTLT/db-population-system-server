from flask import Blueprint

bp = Blueprint('land_subsidy', __name__)

from . import import_land_subsidy  # noqa: E402,F401
from . import list_land_subsidies  # noqa: E402,F401
from . import get_subsidy_years  # noqa: E402,F401
from . import subsidy_statistics  # noqa: E402,F401
from . import delete_subsidy  # noqa: E402,F401
from . import export_land_subsidy  # noqa: E402,F401
