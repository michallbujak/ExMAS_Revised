import pandas as pd


def maximum_delay(
        requests: pd.DataFrame,
        parameters: dict
):
    """ Calculate maximum delay acceptable for the traveller """
    return list(map(lambda x: x if x >= 0 else 0,
                    (1 / requests['WtS'] - 1) * requests['t_ns'] +
                    (parameters['price'] * parameters['share_discount'] *
                     requests['distance'] / 1000) / (requests['VoT'] * requests['WtS'])))


def ride_output_columns():
    return ['ids', 'u_traveller_total', 'u_traveller_individual',
            'veh_distance', 'kind', 't_travel', 'delays',
            'origin_order', 'destination_order']


def pairs_calculation_ride():
    return ['origin', 'destination', 't_ns', 't_req_int',
            'distance', 'VoT', 'WtS', 'max_delay', 'u_ns', 'ASC_pool']

