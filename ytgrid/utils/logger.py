import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler("ytgrid.log"),
        logging.StreamHandler()
    ]
)

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)
