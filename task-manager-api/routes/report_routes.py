from flask import Blueprint, jsonify

from config.constants import ROLE_ADMIN, ROLE_MANAGER
from controllers import report_controller
from middlewares.auth import roles_required, self_or_roles

report_bp = Blueprint('reports', __name__)


@report_bp.get('/reports/summary')
@roles_required(ROLE_ADMIN, ROLE_MANAGER)
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.get('/reports/user/<int:user_id>')
@self_or_roles(ROLE_ADMIN, ROLE_MANAGER)
def user_report(user_id):
    return jsonify(report_controller.user_report(user_id)), 200
