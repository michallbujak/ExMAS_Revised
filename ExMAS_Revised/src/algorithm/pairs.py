""" Part of algorithm, where one calculates feasible pairs """

import pandas as pd
from logging import Logger
import math

from utilities.general_utils import optional_log
from algorithm.miscellaneous import pairs_calculation_ride


def pair_pool(
        requests: pd.DataFrame,
        params: dict,
        skim_matrix: pd.DataFrame,
        logger: Logger | None
):
    """ Calculate pooling combinations of degree two """
    sizes = {'initial': math.pow(len(requests), 2)}
    sizes['current'] = sizes['initial']
    sizes['prev_step'] = sizes['initial']

    optional_log(10, "Calculating values for pairs ...", logger)
    out = pd.DataFrame(index=pd.MultiIndex.from_product(requests['traveller_id'] * 2))
    cols = pairs_calculation_ride()
    for num, ij in enumerate(['_i', '_j']):
        out[[c + ij for c in cols]] = requests.loc[[requests[c] for c in cols]]
        out[ij] = out.index.get_level_values(num)

    out = out[~out['i'] == out['j']]

    # Reduce size of the skim (distances) matrix
    skim_indexes = set(requests['origin'].append(requests['destination']))
    skim = skim_matrix.loc[skim_indexes, skim_indexes].copy()

    # Convert distances to travel time
    skim = skim.div(params["speed"]).astype(int)

    # If user provides a planning horizon, conduct corresponding filtering
    if params.get('horizon', 0) > 0:
        out = out[abs(out['t_since_t0_i'] - out['t_since_t0_j']) < params['horizon']]
        sizes['current'] = len(out)
        optional_log(20, f"Horizon criterion removed "
                         f"{sizes['current'] - sizes['prev_step']}",
                     logger)
        sizes['prev_step'] = len(out)

    out['t_oo'] = out.apply(lambda x: skim.loc[x['origin_i'], x['origin_j']], axis=1)
    out['t_ij'] = out.apply(lambda x: skim.loc[x['origin_j'], x['destination_i']], axis=1)
    out['t_ji'] = out.apply(lambda x: skim.loc[x['origin_i'], x['destination_j']], axis=1)
    out['t_dd'] = out.apply(lambda x: skim.loc[x['destination_i'], x['destination_j']], axis=1)

    # Query based on travellers' acceptable time windows
    query_prompt = '(t_req_int_j + max_delay_j >= t_req_int_i - max_delay_i) &' \
                   ' (t_req_int_j - max_delay_j <= (t_req_int_i + t_ns_i + max_delay_i))'
    out = out.query(query_prompt)


def utility_shared(
        ride_row: pd.Series,
        fifo_lifo: str,
        params: dict
):
    ride_row

