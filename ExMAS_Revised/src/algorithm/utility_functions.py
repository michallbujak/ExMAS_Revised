""" Functions to calculate utility - (un)attractiveness
of shared rides """
import pandas as pd


def utility_pairs(
        ride_row: pd.Series,
        i_j: str,
        fifo_lifo: str,
        params: dict
):
    """ Utility of a shared ride """
    out = -params['price'] * ride_row['distance'] / 1000 * (1 - params['share_discount'])
    out -= ride_row['VoT'] * (ride_row['t_s_' + i_j + '_' + fifo_lifo] * ride_row['WtS'])
    out -= ride_row['VoT'] * ride_row['delay_' + i_j] * \
           ride_row['VoT'] * params.get('delay_value')
    out -= ride_row['ASC_pool_' + i_j]
    return out


def utility_shared(
        distance: float,
        vot: float,
        wts: float,
        price: float,
        discount: float,
        delay: float,
        delay_value: float,
        asc_pool: float,
        avg_speed: float
) -> float:
    """ Calculate utility of a shared ride """
    time = distance/avg_speed
    out = -price * distance / 1000 * (1 - discount)
    out -= vot*time*wts + vot*delay*delay_value
    out -= asc_pool
    return out
