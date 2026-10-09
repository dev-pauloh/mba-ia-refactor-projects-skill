from flask import Blueprint

from utils.helpers import utcnow

system_bp = Blueprint('system', __name__)


@system_bp.get('/health')
def health():
    return {'status': 'ok', 'timestamp': str(utcnow())}


@system_bp.get('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
