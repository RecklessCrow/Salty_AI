import logging
import time

logger = logging.getLogger('myapp')

hdlr = logging.FileHandler('./logs/match_history.log')
formatter = logging.Formatter('%(asctime)s %(message)s', "%m-%d-%Y (%H:%M)")
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

logger.error('We have a problem')
logger.info('While this is just chatty')
logger.info('While this is just chatty')