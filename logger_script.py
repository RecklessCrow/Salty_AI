import logging

logger = logging.getLogger('myapp')

hdlr = logging.FileHandler('./logs/match_history.log')
formatter = logging.Formatter('%(asctime)s %(message)s', "%m-%d-%Y (%H:%M)")
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    logger.log()