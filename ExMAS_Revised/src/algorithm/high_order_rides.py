""" Search for feasible extensions """
from itertools import combinations, product
from logging import Logger

import pandas as pd

from utilities.general_utils import optional_log, calculate_distance
from utility_functions import utility_shared


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

    optional_log(20, f'Initial number of rides of degree {current_degree}'
                     f'is {len(cur_rides)}', logger)

    all_combinations = cur_rides['indexes'].to_list()

    # Check for each ride whether it is extendable
    # Based on shareability structures, example
    # (A, B, C) might be feasible only if (A, B),
    # (B, C) and (A, C) are feasible

    def overlap_func(comb1, comb2, deg):
        if comb1 == comb2:
            return False
        return sum([t in comb2 for t in comb1]) == deg

    ext_trav_from_ride = {}

    for cur_comb in all_combinations:
        overlap_list = [c for c in cur_comb if
                        overlap_func(cur_comb, c, current_degree - 1)]
        # If we want a ride of degree n+1, we need (n+1 choose n) = n+1
        # combinations to be feasible. Hence, apart from the one in loop
        # we need additional n. There might be k different extensions
        # to consider, hence k*(n+1 choose n) (separately order
        # of origins and destinations)
        if len(overlap_list) < current_degree:
            ext_trav_from_ride[cur_comb] = False
            continue

        ext_trav_from_ride[cur_comb] = []

        for overlapping in overlap_list:
            new = set(cur_comb + overlapping).difference(set(cur_comb))
            if not new | new in ext_trav_from_ride[cur_comb]:
                ext_trav_from_ride[cur_comb].append(new)

    if not ext_trav_from_ride:
        return pd.DataFrame(), False

    # Filter for the rides, where the order is proper,
    # i.e. the rides must hold the same order of origins
    # and destinations. If there is no overlap in the order,
    # the combination will not be feasible
    cur_rides = cur_rides.loc[
        cur_rides.apply(lambda x: x['indexes'] in ext_trav_from_ride.keys(), axis=1)
    ]

    extensions = []
    browsed = []

    origin_combs_all = cur_rides['origin_order'].to_list()
    destination_combs_all = cur_rides['destination_order'].to_list()

    # There might be different destinations sequences feasible for
    # each origin combinations
    orig_dest = {}
    for orig, dest in zip(origin_combs_all, destination_combs_all):
        if orig in orig_dest.keys():
            orig_dest[orig].append(dest)
        else:
            orig_dest[orig] = [dest]

    for ride in cur_rides:
        for extension in ext_trav_from_ride[ride['indexes']]:
            for orig_no, dest_no in product(range(current_degree + 1),
                                            range(current_degree + 1)):
                origins = ride['origin_order'].copy()
                origins.insert(orig_no, extension)
                destinations = ride['destination_order'].copy()
                destinations.insert(dest_no, extension)

                if (origins, destinations) in browsed:
                    continue

                for comb_origins in combinations(origins, current_degree):
                    if not comb_origins in origin_combs_all:
                        flag_ok = False
                        break
                    dest_temp = destinations.copy()
                    dest_temp.pop(set(dest_temp).difference(set(comb_origins)))
                    if dest_temp in orig_dest[comb_origins]:
                        flag_ok = True
                    else:
                        flag_ok = False
                        break
                if flag_ok:
                    browsed.append((origins, destinations))
                    extensions.append((origins, destinations))
                else:
                    browsed.append((origins, destinations))

    optional_log(20, f'Number of feasible extensions of degree {current_degree}'
                     f' is {len(extensions)}', logger)

    if not extensions:
        return pd.DataFrame(), False

    # Check for utility, first assuming 0 delay
    for extension in extensions:
        private_chars = {
            t: {
                char: requests.loc[t, char]
                for char in ['distance', 'VoT', 'WtS', 'u_ns', 'ASC_pool']
            } for t in extension[0],
        }
        ind_dist = {
            t: calculate_distance(skim=skim_matrix,
                                  list_points=extension[0][extension[0].index(t):] +
                                  extension[1][:(1+extension[1].index(t))]
                                  )
            for t in extension[0]
        }

        # First if no delay
        shared_utilities = {
            t: utility_shared(
                distance=ind_dist[t]['distance'],
                vot=private_chars[t]['VoT'],
                wts=private_chars[t]['WtS'],
                price=params['price'],
                discount=params['share_discount'],
                delay=0,
                delay_value=params['delay_value'],
                asc_pool=private_chars[t]['ASC_pool'],
                avg_speed=params['speed']
            ) for t in extension[0]
        }

        if any([shared_utilities[key] < private_chars[key]['u_ns']
                for key in private_chars.keys()]):
            continue



