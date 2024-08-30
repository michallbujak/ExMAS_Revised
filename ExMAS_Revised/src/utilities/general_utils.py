""" General purpose functions """

import logging
import os

import pandas as pd


def optional_log(
        level: int,
        msg: str,
        logger: logging.Logger or None
) -> None:
    """ Log things only if a Logger is passed """

    if logger is None:
        pass
    else:
        logger.log(level, msg)


def create_folder(
        path: str,
        logger: logging.Logger or None = None
) -> None:
    """
    Designed to create a folder under given path
    :param path: a path to create a folder
    :param logger: logging purposes
    :return:
    """
    try:
        os.mkdir(path)
    except OSError:
        pass
    else:
        optional_log(30, f'Creating folder at {path}', logger)


def calculate_distance(
        skim: pd.DataFrame,
        list_points: list or tuple
) -> float or int:
    """
    Function designed to calculate distance
    when going through multiple points
    """
    assert list_points, "Empty list of points"
    if len(list_points) == 1:
        return 0
    out = 0
    current_point = 0
    next_point = 1
    while next_point <= len(list_points):
        out += skim.loc[list_points[current_point], list_points[next_point]]
        current_point += 1
        next_point += 1
    return out
