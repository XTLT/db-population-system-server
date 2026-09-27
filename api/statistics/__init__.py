from flask import Blueprint

bp = Blueprint('statistics', __name__)

from . import statistics
from . import stats
from . import students
from . import students_statistics
from . import statistics_trend
from . import statistics_distribution
from . import statistics_comparison
from . import statistics_age_distribution
from . import statistics_by_village
