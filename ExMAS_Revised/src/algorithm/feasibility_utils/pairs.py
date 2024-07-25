""" Part of algorithm, where one calculates feasible pairs """
from logging import Logger
import math
from itertools import product

import pandas as pd

from algorithm.feasibility_utils.utility_functions import utility_pairs
from utilities.general_utils import optional_log
from algorithm.feasibility_utils.miscellaneous import pairs_calculation_ride, ride_output_columns
from algorithm.feasibility_utils.pooltype import PoolType


def pair_pool(
        requests: pd.DataFrame,
        params: dict,
        skim_matrix: pd.DataFrame,
        logger: Logger | None
):
    """ Calculate pooling combinations of degree two """
    sizes = {'initial': 4 * math.pow(len(requests), 2)}
    sizes['current'] = sizes['initial']
    sizes['prev_step'] = sizes['initial']

    optional_log(20, "Calculating values for pairs ...", logger)

    pairs = pd.DataFrame(index=pd.MultiIndex.from_product([requests['traveller_id']] * 2))
    cols = pairs_calculation_ride()
    for num, ij in enumerate(['_i', '_j']):
        pairs[[c + ij for c in cols]] = requests.loc[[requests[c] for c in cols]]
        pairs[ij] = pairs.index.get_level_values(num)

    pairs = pairs[~pairs['i'] == pairs['j']]

    # Reduce size of the skim (distances) matrix
    skim_indexes = set(requests['origin'].append(requests['destination']))
    skim = skim_matrix.loc[skim_indexes, skim_indexes].copy()

    # Convert distances to travel time
    skim = skim.div(params["speed"]).astype(int)

    # If user provides a planning horizon, conduct corresponding filtering
    if params.get('horizon', 0) > 0:
        pairs = pairs[abs(pairs['t_since_t0_i'] - pairs['t_since_t0_j']) < params['horizon']]
        sizes['current'] = 2 * len(pairs)
        optional_log(0, f"Horizon criterion removed "
                        f"{sizes['current'] - sizes['prev_step']}",
                     logger)
        sizes['prev_step'] = 2 * len(pairs)

    # Query based on travellers' acceptable time windows (departure compatibility)
    query_prompt = '(t_req_int_j + max_delay_j >= t_req_int_i - max_delay_i) &' \
                   ' (t_req_int_j - max_delay_j <= (t_req_int_i + t_ns_i + max_delay_i))'
    pairs = pairs.query(query_prompt)

    # Calculate and filter for origin compatibility
    pairs['t_oo'] = pairs.apply(
        lambda x: int(skim.loc[x['origin_i'], x['origin_j']] / params['speed']),
        axis=1
    )
    query_prompt = '(t_req_int_i + t_oo + max_delay_i >= t_req_int_j - max_delay_j) &' \
                   ' (t_req_int_i + t_oo - max_delay_i <= (t_req_int_j + max_delay_j))'
    pairs = pairs.query(query_prompt)

    sizes['current'] = 2 * len(pairs)
    optional_log(0,
                 f"Initial filtering reduced size from "
                 f"{sizes['prev_step']} to {sizes['current']}",
                 logger)
    sizes['prev_step'] = sizes['current']

    # Determine whether 2nd origin is reachable within accepted time
    pairs['delay'] = pairs['t_req_int_i'] + pairs['t_oo'] + pairs['t_req_int_j']
    pairs['delay_i'] = pairs.apply(
        lambda x: min(abs(x['delay'] / 2), x['max_delay_i'], x['max_delay_i']) *
                  (1 if x['delay'] < 0 else -1),
        axis=1
    )

    for ij in ['i', 'j']:
        pairs = pairs[abs(pairs['delay_' + ij]) <= pairs['delta_' + ij] / params['delay_value']]

    sizes['current'] = 2 * len(pairs)
    optional_log(0, f"Origin compatibility filtered from {sizes['prev_step']}"
                    f"to {sizes['current']}.", logger)
    sizes['prev_step'] = sizes['current']

    # Compute trip characteristics
    pairs['t_ij'] = pairs.apply(
        lambda x: int(skim.loc[x['origin_j'], x['destination_i']] / params['speed']),
        axis=1
    )
    pairs['t_ji'] = pairs.apply(
        lambda x: int(skim.loc[x['origin_i'], x['destination_j']] / params['speed']),
        axis=1
    )
    pairs['t_dd'] = pairs.apply(
        lambda x: int(skim.loc[x['destination_i'], x['destination_j']] / params['speed']),
        axis=1
    )

    optional_log(10, 'Travel times calculated', logger)

    # Now check for utilities with FIFO and LIFO
    for ij, fl in product(['i', 'j'], ['fifo', 'lifo']):
        # First, calculate time
        pairs['t_s_' + ij + '_' + fl] = pairs.apply(
            travel_times,
            i_j=ij,
            fifo_lifo=fl,
            axis=1
        )
        # Now proceed to utility
        pairs['u_s_' + ij + '_' + fl] = pairs.apply(
            utility_pairs,
            i_j=ij,
            fifo_lifo=fl,
            axis=1
        )

    optional_log(10, 'Utilities for pairs calculated', logger)

    # Extract attractive FIFO and LIFO rides
    for fl in ['fifo', 'lifo']:
        pairs[fl + '_attractive'] = pairs.apply(
            check_attractiveness,
            fifo_lifo=fl,
            axis=1
        )

    return pd.concat([extract_attractive(pairs, t, params) for t in ['fifo', 'lifo']])


def travel_times(
        ride_row: pd.Series,
        i_j: str,
        fifo_lifo: str
):
    """ Calculate travel times """
    if i_j == 'i':
        time = ride_row['t_oo']
        if fifo_lifo == 'fifo':
            return time + ride_row['t_ji']
        return time + ride_row['t_ns_j'] + ride_row['t_dd']
    else:
        if fifo_lifo == 'fifo':
            return ride_row['t_ji'] + ride_row['t_dd']
        return ride_row['t_ns_j']


def check_attractiveness(
        ride_row: pd.Series,
        fifo_lifo: str
):
    """ Check whether shared ride is more attractive in fifo/lifo """
    return (ride_row['u_s_i_' + fifo_lifo] < ride_row['u_ns_i']) & \
        (ride_row['u_s_j' + fifo_lifo] < ride_row['u_ns_j'])


def extract_attractive(
        rides: pd.DataFrame,
        fifo_lifo: str,
        parameters: dict
):
    """ Extract to desired output """
    attractive = rides.loc[rides[fifo_lifo + '_attractive']]
    out = pd.DataFrame(columns=ride_output_columns(), index=attractive.index)
    out['ids'] = out.apply(lambda x: [x['i'], x['j']], axis=1)
    out['u_traveller_individual'] = out.apply(
        lambda x: [x['u_s_i_' + fifo_lifo], x['u_s_j_' + fifo_lifo]],
        axis=1
    )
    out['u_traveller_total'] = out['u_traveller_individual'].apply(lambda x: sum(x))
    out['veh_distance'] = out['t_travel'] * parameters['speed']
    out['origin_order'] = out.apply(lambda x: [x['i'], x['j']], axis=1)
    out['delays'] = out.apply(lambda x: [x['delay_i'], x['delay_j']], axis=1)
    if fifo_lifo == 'fifo':
        out['t_travel'] = out['t_oo'] + out['t_ij'] + out['t_dd']
        out['destination_order'] = out.apply(lambda x: [x['i'], x['j']], axis=1)
        out['kind'] = PoolType.FIFO2
    else:
        out['t_travel'] = out['t_oo'] + out['t_ns_j'] + out['t_dd']
        out['destination_order'] = out.apply(lambda x: [x['j'], x['i']], axis=1)
        out['kind'] = PoolType.LIFO2

    return out


