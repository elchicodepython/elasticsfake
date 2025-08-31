import logging


def configure_logger(conf: dict) -> logging.Logger:
    log_level = conf.get("app.logging.level", "INFO")
    log_format = conf.get(
        "app.logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    log_file = conf.get("app.logging.file", "elasticsfake.log")
    max_bytes = conf.get(
        "app.logging.max_bytes_before_rotation", 10 * 1024 * 1024
    )  # 10 MB
    backup_count = conf.get("app.logging.rotated_log_files", 5)

    logger = logging.getLogger("elasticsfake")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    formatter = logging.Formatter(log_format)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger
