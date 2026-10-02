import os
import logging

from flask import Blueprint
from config import BASE_DIR

logger = logging.getLogger('population_system')
PHOTO_UPLOAD_DIR = os.path.join(BASE_DIR, 'Photos')
os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)

bp = Blueprint('photos', __name__)

from . import upload_photo_by_id_card
from . import upload_photo
from . import get_photo
from . import delete_photo
from . import get_photo_by_type
from . import delete_photo_by_type
from . import serve_photo
from . import get_person_photos
from . import batch_delete_photos
