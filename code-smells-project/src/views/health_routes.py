from flask import Blueprint, current_app, jsonify

from src.controllers import health_controller

bp = Blueprint("health", __name__)


@bp.get("/")
def index():
    return jsonify(health_controller.indice())


@bp.get("/health")
def health_check():
    return jsonify(health_controller.status(current_app.config["APP_ENV"])), 200
