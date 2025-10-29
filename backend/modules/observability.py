import logging


def get_logger(name: str) -> logging.Logger:
    # loki_logs_handler = logging_loki.LokiHandler(
    #     url=LOKI_ENDPOINT,
    #     tags={"app": name},
    #     version="1",
    # )
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # logger.addHandler(loki_logs_handler)
    return logger
    