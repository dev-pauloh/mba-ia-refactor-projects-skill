import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import system_bp
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.notification_service import NotificationService
from services.token_service import TokenService


def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    token_service = TokenService(settings.SECRET_KEY, settings.TOKEN_MAX_AGE)
    notification_service = NotificationService(
        settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD,
    )
    app.extensions['token_service'] = token_service

    app.register_blueprint(create_task_blueprint(TaskController(notification_service)))
    app.register_blueprint(create_user_blueprint(UserController(token_service)))
    app.register_blueprint(create_report_blueprint(ReportController()))
    app.register_blueprint(create_category_blueprint(CategoryController()))
    app.register_blueprint(system_bp)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    create_app().run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
