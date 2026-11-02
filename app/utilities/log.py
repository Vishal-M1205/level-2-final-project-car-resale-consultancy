import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        format="%(asctime)s : %(name)s : %(levelname)s : %(message)s",
    )
