import pandas as pd

from algorithm.pooltype import PoolType


def single_rides(
        requests: pd.DataFrame
):
    """ Assume that private rides are always feasible """
    output = requests.copy()
    output['ids'] = output['traveller_id'].apply(lambda x: [x])
    output['u_traveller_total'] = output['u_ns']
    output['u_traveller_individual'] = output['u_ns'].apply(lambda x: [x])
    output['veh_distance'] = output['distance']
    output['kind'] = PoolType.SINGLE
    output['t_travel'] = output['t_ns'].apply(lambda x: [x])
    output['delays'] = [[0]]*len(output)
    output['origin_order'] = output['traveller_id'].apply(lambda x: [x])
    output['destination_order'] = output['origin_order']

    return output.copy()
