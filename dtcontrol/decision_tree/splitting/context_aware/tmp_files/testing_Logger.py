import logging

logger = logging.getLogger("PredicateParser_logger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(message)s')
file_handler = logging.FileHandler('PredicateParser_logger.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


logger.warning("TEST")
