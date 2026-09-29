from flask import Blueprint

bp = Blueprint('persons', __name__)

from . import lookup_all
from . import list_persons
from . import search
from . import search_advanced
from . import check_duplicate
from . import family
from . import get_person
from . import add_person
from . import update_person
from . import delete_person
from . import save_education
from . import migrate_person
from . import split_household
from . import merge_household
from . import add_household
from . import new_hu_hao
from . import batch_delete
from . import batch_update
from . import deleted
