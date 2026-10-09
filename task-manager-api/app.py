import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import init_db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService
from services.token_service import TokenService


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    init_db(app)
    app.extensions['token_service'] = TokenService(settings.SECRET_KEY, settings.TOKEN_MAX_AGE)
    app.extensions['notification_service'] = NotificationService(
        settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD
    )

    register_error_handlers(app)
    for blueprint in (system_bp, task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
