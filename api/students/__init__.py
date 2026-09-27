from flask import Blueprint

bp = Blueprint('students', __name__)

from . import get_student
from . import create_student
from . import update_student
from . import delete_student
from . import search_students
from . import batch_delete_students
from . import batch_update_students
from . import import_students
from . import export_students
from . import promote_grades
from . import download_student_template
