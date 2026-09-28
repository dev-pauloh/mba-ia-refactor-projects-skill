import logging

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Servidor iniciado em http://%s:%s", app.config["HOST"], app.config["PORT"]
    )
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
