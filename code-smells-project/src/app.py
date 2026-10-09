from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.database.connection import init_db
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


def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)

    if app.config["CORS_ORIGINS"]:
        CORS(app, origins=app.config["CORS_ORIGINS"])

    init_db(app)
    register_error_handlers(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    return app
