""" Main script for calling the ExMAS_Revised loop """

import utilities.preprocessing
from utilities.general_utils import initialise_logger


def exmas_revised(
        configuration_path: str,
) -> dict:
    """ Main caller of the algorithm
    @param configuration_path: path to the .json configuration file
    @return computed results
    """
    configuration = utilities.preprocessing.load_configuration(path=configuration_path)
    main_logger = initialise_logger(logger_level=configuration.get('logger_level', 'INFO'))
    skim_matrix = utilities.preprocessing.load_skim(
        config=configuration, logger=main_logger)
    demand = utilities.preprocessing.load_demand(
        configuration['requests'], config=configuration, logger=main_logger)

    x = 0

    return {}

exmas_revised('configs/runs/run_nyc.json')