""" Search for feasible extensions """
from itertools import combinations
from logging import Logger

import pandas as pd


def extend_feasible_rides(
        feasible_rides: pd.DataFrame,
        requests: pd.DataFrame,
        params: dict,
        skim_matrix: pd.DataFrame,
        logger: Logger | None
) -> (pd.DataFrame, bool):
    """
    Extend feasible rides of degree 2 or more
    accounting for their attractiveness
    :param feasible_rides: dataframe with current feasible rides
    :param requests: original requests
    :param params: parameters of the simulation
    :param skim_matrix: distances within the city
    :param logger: for logging purposes
    :return: extended list of rides with their characteristics
    and information whether the extension was successful
    (can be further propagated) or is to be terminated
    """
    # Manipulate data for easier implementation.
    characteristics = requests.apply(
        lambda x: x['traveller_id', 'VoT', 'WtS', 't_ns'],
        axis=1
    )
    characteristics = {
        x[0]: {
            'VoT': x[1],
            'WtS': x[2],
            't_ns': x[3]
        } for x in characteristics
    }
    # obtain the latest extension, i.e. maximum degree
    current_degree = max(feasible_rides['indexes'].apply(
        lambda x: len(x)
    ))

    is_max_degree = feasible_rides['index'].apply(
        lambda x: len(x) == current_degree
    )

    cur_rides = feasible_rides.loc[is_max_degree].copy()

    cur_combinations = feasible_rides['indexes'].to_list()

    # Check for each ride whether it is extendable
    # Based on shareability structures, example
    # (A, B, C) might be feasible only if (A, B),
    # (B, C) and (A, C) are feasible

    def overlap_func(comb1, comb2, deg):
        if comb1 == comb2:
            return False
        return sum([t in comb2 for t in comb1]) == deg

    extension_combinations = []

    for cur_combination in cur_combinations:
        overlap_list = [c for c in cur_combination if
                        overlap_func(cur_combination, c, current_degree-1)]
        # If we want a ride of degree n+1, we need (n+1 choose n) = n+1
        # combinations to be feasible. Hence, apart from the one in loop
        # we need additional n. There might be k different extensions
        # to consider, hence k*(n+1 choose n)
        if len(overlap_list) < current_degree:
            continue
        for overlapping in overlap_list:
            new = list(set(cur_combination + overlapping))
            if new in extension_combinations:
                continue
            else:
                extension_combinations.append(new)

    # Now we have combinations of travellers, but we need to consider
    # different origin and destination orders.


