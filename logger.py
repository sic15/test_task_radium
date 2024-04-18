import logging

logger = logging.getLogger()

logging.basicConfig(
        level=logging.INFO,
        filename='logs.log',
        filemode='a',
        format='%(asctime)s: %(name)s - %(levelname)s - %(message)s'
    )