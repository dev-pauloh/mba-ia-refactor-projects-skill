import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from src.app import create_app  # noqa: E402  (logging precisa estar configurado antes da config)
from src.config.settings import Settings  # noqa: E402

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", Settings.HOST, Settings.PORT)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
