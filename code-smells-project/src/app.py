import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.database import connection
from src.middlewares.error_handler import register_error_handlers
from src.views import admin_routes, health_routes, pedido_routes, produto_routes, relatorio_routes, usuario_routes

BLUEPRINTS = (
    produto_routes.bp,
    usuario_routes.bp,
    pedido_routes.bp,
    relatorio_routes.bp,
    health_routes.bp,
    admin_routes.bp,
)


def create_app(settings=None):
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Flask(__name__)
    app.config.from_object(settings)

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    connection.init_app(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    register_error_handlers(app)
    return app
