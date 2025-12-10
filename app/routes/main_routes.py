from flask import Blueprint
from app.controllers.main_controller import index
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index_route():
    logger.info("Main index route accessed")
    return index()
