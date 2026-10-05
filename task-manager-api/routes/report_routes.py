from flask import Blueprint, g, jsonify

from middlewares.auth import require_auth


def create_report_blueprint(controller):
    bp = Blueprint('reports', __name__)

    @bp.get('/reports/summary')
    @require_auth(admin=True)
    def summary_report():
        return jsonify(controller.summary()), 200

    @bp.get('/reports/user/<int:user_id>')
    @require_auth()
    def user_report(user_id):
        return jsonify(controller.user_report(user_id, g.current_user)), 200

    return bp
