import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def create_logger():
    logger_ = logging.getLogger(None)
    logger_.setLevel(logging.DEBUG)

    log_file = (Path(__file__).parent / "..").resolve() / "data" / "tuxpay.log"
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler
    fh = TimedRotatingFileHandler(log_file, when='W6')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger_.addHandler(fh)

    # Stdout
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger_.addHandler(sh)
    return logger_


logger = create_logger()
