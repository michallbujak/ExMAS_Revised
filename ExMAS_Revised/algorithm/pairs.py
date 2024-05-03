import pandas as pd
from logging import Logger

from ExMAS_Revised.algorithm.pooltype import PoolType
from ExMAS_Revised.utilities.general_utils import optional_log
from ExMAS_Revised.algorithm.miscellaneous import ride_columns


def pair_pool(
        requests: pd.DataFrame,
        parameters: dict,
        logger: Logger or None
):
    """ Calculate pooling combinations of degree two """

    optional_log(10, "Calculating values for pairs ...", logger)
    r = pd.DataFrame(index=pd.MultiIndex.from_product(requests['traveller_id']*2))
    cols = ride_columns()
    for num, ij in enumerate(['_i', '_j']):
        # out[[c + ij for c in cols]] = requests.loc[]
        # TODO
        pass
