import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

log_file = (Path(__file__).parent / "..").resolve() / "data" / "tuxpay.log"

# File handler
fh = TimedRotatingFileHandler(log_file, when='W6')
fh.setLevel(logging.DEBUG)

# Stdout
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(sh)
