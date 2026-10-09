from flask import Blueprint, jsonify

from src.controllers import health_controller
from src.middlewares.auth import require_auth

bp = Blueprint("health", __name__)


@bp.get("/")
def index():
    return jsonify(health_controller.index())


@bp.get("/health")
@require_auth
def health_check():
    return jsonify(health_controller.health()), 200
