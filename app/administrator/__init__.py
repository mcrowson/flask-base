from flask import Blueprint

admin = Blueprint('administrator', __name__)

from . import views  # noqa
