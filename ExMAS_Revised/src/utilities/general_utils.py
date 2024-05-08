import logging


def optional_log(
        level: int,
        msg: str,
        logger: logging.Logger or None
):
    """ Log things only if a Logger is passed """

    if logger is None:
        pass
    else:
        logger.log(level, msg)
    