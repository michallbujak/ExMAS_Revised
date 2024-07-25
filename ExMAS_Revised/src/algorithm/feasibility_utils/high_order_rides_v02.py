""" Search for feasible extensions """
from collections import Counter
from itertools import product
from logging import Logger

import pandas as pd
import numpy as np

from utilities.general_utils import optional_log, calculate_distance
from algorithm.feasibility_utils.utility_functions import utility_shared
from algorithm.feasibility_utils.miscellaneous import ride_output_columns


def extend_feasible_rides(
        feasible_rides: pd.DataFrame,
        requests: pd.DataFrame,
        params: dict,
        skim_matrix: pd.DataFrame,
        logger: Logger | None
) -> pd.DataFrame:
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
    # obtain the latest extension, i.e. maximum degree
    current_degree = max(feasible_rides['indexes'].apply(
        lambda x: len(x)
    ))

    is_max_degree = feasible_rides['index'].apply(
        lambda x: len(x) == current_degree
    )

    rides_to_extend = feasible_rides.loc[is_max_degree].copy()

    optional_log(20, f'Initial number of rides of degree {current_degree}'
                     f'is {len(rides_to_extend)}', logger)

    # Move to feasible extensions
    combinations = rides_to_extend.apply(
        lambda row: (row['indexes'], row['origin_order'], row['dest_order']),
        axis=1
    )

    def _compatible_func(_comb1, _comb2, _deg):
        _common = [t for t in _comb2[0] if t in _comb1[0]]
        if len(_common) != _deg - 1:
            return []
        if [t for t in _comb1[1] if t in _common] != [t for t in _comb2[1] if t in _common]:
            return []
        if [t for t in _comb1[2] if t in _common] != [t for t in _comb2[2] if t in _common]:
            return []
        _new_sec = [t for t in _comb2[0] if t not in _common]
        return np.prod([_comb1[1].insert(_comb2[1].index(_new_sec), _new_sec),
                        _comb1[1].insert(_comb2[1].index(_new_sec) + 1, _new_sec)],
                       [_comb1[2].insert(_comb2[2].index(_new_sec), _new_sec),
                        _comb1[2].insert(_comb2[2].index(_new_sec) + 1, _new_sec)])

    all_od_pairs = [_compatible_func(c1, c2, current_degree) for c1, c2 in product(combinations, combinations)]
    all_od_pairs = [a for b in all_od_pairs for a in b if b]
    counted_od_pairs = Counter(all_od_pairs)
    candidate_combinations = [k for k, v in counted_od_pairs.items() if v >= current_degree]

    optional_log(20, f'Number of feasible extensions of degree {current_degree}'
                     f' is {len(candidate_combinations)}', logger)

    if not candidate_combinations:
        return pd.DataFrame()

    feasible_combinations = {}

    for extension in candidate_combinations:
        private_chars = {
            t: {
                char: requests.loc[t, char]
                for char in ['distance', 'VoT', 'WtS', 'u_ns', 'ASC_pool']
            } for t in extension[0],
        }
        ind_dist = {
            t: calculate_distance(skim=skim_matrix,
                                  list_points=[requests.loc[t, 'origin'] for t in
                                               extension[0][extension[0].index(t):]] +
                                              [requests.loc[t, 'destination'] for t in
                                               extension[1][:(1 + extension[1].index(t))]]
                                  )
            for t in extension[0]
        }

        # First, calculate delays
        start_time = requests.loc[extension[0][0], 't_req_int']
        initial_delays = [requests.loc[t, 't_req_int'] - start_time for t in extension[0]]
        optimal_delay = -sum(initial_delays) / len(initial_delays)
        delays = [abs(t + optimal_delay) for t in initial_delays]

        # Now, utility
        shared_utilities = {
            t: utility_shared(
                distance=ind_dist[t]['distance'],
                vot=private_chars[t]['VoT'],
                wts=private_chars[t]['WtS'],
                price=params['price'],
                discount=params['share_discount'],
                delay=delays[num],
                delay_value=params['delay_value'],
                asc_pool=private_chars[t]['ASC_pool'],
                avg_speed=params['speed']
            ) for num, t in enumerate(extension[0])
        }

        if any([shared_utilities[key] < private_chars[key]['u_ns']
                for key in private_chars.keys()]):
            continue

        feasible_combinations[extension] = {
            'ids': extension[0],
            'u_traveller_total': sum(shared_utilities),
            'u_traveller_individual': list(shared_utilities.values()),
            'veh_distance': calculate_distance(skim_matrix,
                                               [requests.loc[t, 'origin'] for t in extension[0]] +
                                               [requests.loc[t, 'destination'] for t in extension[1]]
                                               ),
            'kind': int(str(current_degree) + str(extension[1].index(extension[0][0]))),
            'delays': delays,
            'origin_order': extension[0],
            'destination_order': extension[1]
        }
        feasible_combinations[extension]['t_travel'] = \
            feasible_combinations[extension]['veh_distance'] * params['speed']

        out = pd.DataFrame(feasible_combinations).transpose()

        return out[ride_output_columns()]
