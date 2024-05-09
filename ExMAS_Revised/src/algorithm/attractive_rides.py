""" Script with main ExMAS calculations """
from logging import Logger

import pandas as pd

from algorithm.miscellaneous import maximum_delay, ride_output_columns
from algorithm.singles import single_rides
from utilities.general_utils import optional_log
from algorithm.pairs import pair_pool


def attractive_rides(
        requests: pd.DataFrame,
        skim_matrix: pd.DataFrame,
        parameters: dict,
        travellers_characteristics: dict | None = None,
        logger: Logger | None = None
):
    """
    The main function of the ExMAS algorithm
    :param requests: request dataframe. The dataframe must contain
    the following columns: origin, destination, request_time
    optionally it can include passenger id for identification purposes;
    the key word is "traveller_id".
    :param skim_matrix: matrix with distances between nodes
    :param parameters: params required in the process
    those include: speed, price, share_discount, horizon
    :param travellers_characteristics: dictionary with individual
    traits of travellers. Passed optionally. If passed, the passenger
    id must be passed in the request file and must coincide with the
    passed dictionary, the key word is "traveller_id".
    :param logger: if you want to receive log, pass a Logger
    :return: dictionary with ride-pooling system estimates
    mainly: shareability graph ('feasible_rides') and schedule
    for the optimal performance ('schedule')
    """

    # Incorporate individual characteristics if passed
    individual_characteristics = ['VoT', 'WtS']
    if travellers_characteristics is not None:
        assert 'traveller_id' in requests.columns, "You need to specify 'traveller_id'"
        assert any(t in travellers_characteristics.columns for t in individual_characteristics), \
            "The two admissible traveller params, i.e. 'VoT' and 'WtS' are missing"

        requests = pd.merge(requests, travellers_characteristics, on="traveller_id")

        for characteristic in individual_characteristics:
            if characteristic not in travellers_characteristics.columns:
                requests[characteristic] = parameters[characteristic]
    else:
        for characteristic in individual_characteristics:
            requests[characteristic] = parameters[characteristic]

    optional_log(10, "VoT and WtS updated", logger)

    if 'traveller_id' not in requests.columns:
        optional_log(0, "travelled_id not specified, defaults", logger)
        requests['traveller_id'] = list(range(1, len(requests) + 1))

    # Compute trip characteristics
    requests['distance'] = requests.apply(
        lambda x: skim_matrix.loc[x['origin'], x['destination']],
        axis=1
    )
    requests['t_req_int'] = requests.apply(
        lambda x: x['request_time'] - min(requests['request_time']),
        axis=1
    )
    requests.sort_values('t_req_int', inplace=True)

    # Compute basic characteristics for the private rides
    requests['t_ns'] = requests['distance'].apply(lambda x: int(x / parameters["speed"]))
    requests['u_ns'] = requests.apply(
        lambda x: parameters['price'] * x['distance'] / 1000 + x['VoT'] * x['t_ns'],
        axis=1
    )

    # Maximum possible delay of a trip, using travellers perspective
    requests['max_delay'] = maximum_delay(
        requests=requests,
        parameters=parameters
    )

    # If not passed, add alternative specific constant for ride-pooling
    if 'ASC_pool' not in requests.columns:
        requests['ASC_pool'] = 0

    # Initialise a shareability graph (dataframe with feasible rides)
    feasible_rides = pd.DataFrame(
        columns=ride_output_columns()
    )

    # Start with single rides
    feasible_rides = pd.concat(
        [feasible_rides,
         single_rides(requests)]
    )

    optional_log(20, "Single rides computed", logger)

    # Proceed to rides of degree 2
    feasible_rides = pd.concat(
        [feasible_rides,
         pair_pool(
             requests=requests,
             params=parameters,
             skim_matrix=skim_matrix,
             logger=logger
         )]
    )


    return feasible_rides

