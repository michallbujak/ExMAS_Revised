""" Simple func"""

from logging import Logger
import json

import pandas as pd
import osmnx as ox
import networkx as nx
import pyarrow

from src.utilities.general_utils import optional_log


def load_configuration(
        path: str,
        logger: Logger or None = None
) -> dict:
    """
    Load configuration files from .json format
    :param path: path to the configuration file
    :param logger: logger for information
    :return: configuration dictionary
    """
    with open(path, encoding='utf-8') as json_file:
        config = json.load(json_file)

    if config.get("nested"):
        for sub_config in ['behaviour', 'city']:
            with open(config[sub_config], encoding='utf-8') as json_file:
                add_config = json.load(json_file)
                config.update(add_config)

    if logger:
        optional_log(30, f"Successfully loaded config from {path}", logger)

    return config


def load_skim(
        config: dict,
        logger: Logger
) -> pd.DataFrame:
    """
    Load data necessarily for distance and paths calculations
    :param config: configuration of the city
    :param logger: for logging purposes
    :return: skim - dictionary with way of calculation and data
    """
    try:
        skim_matrix = pd.read_parquet(config['paths']['skim_matrix'])
    except FileNotFoundError:
        missing_skim = True
        skim_matrix = None
    else:
        missing_skim = False

    if missing_skim:
        try:
            city_graph = nx.read_graphml(config['paths']['city_graph'])
            # city_graph = pickle.load(open(config['paths']['city_graph'], 'rb'))
        except FileNotFoundError:
            logger.warning("City graph missing, using osmnx")
            logger.warning(f"Writing the city graph to {config['paths']['city_graph']}")
            city_graph = ox.graph_from_place(config['city'], network_type='drive')
            ox.save_graphml(city_graph, config['paths']['city_graph'])
            # pickle.dump(city_graph, open(config['paths']['city_graph'], 'wb'))
        else:
            logger.warning("Successfully read city graph")
        logger.warning("Skim matrix missing, calculating...")
        skim_matrix = pd.DataFrame(dict(
            nx.all_pairs_dijkstra_path_length(city_graph, weight='length')))
        skim_matrix.columns = [str(col) for col in skim_matrix.columns]

        logger.warning(f"Writing the skim matrix to {config['paths']['skim_matrix']}")
        skim_matrix.to_parquet(config['paths']['skim_matrix'], compression='brotli')
        config['paths']['skim_matrix'] = config['paths']['skim_matrix']
    else:
        logger.warning("Successfully read skim matrix")

    skim_matrix.columns = [int(t) for t in skim_matrix.columns]

    return skim_matrix


def load_demand(
        path: str,
        config: dict or None = None,
        logger: Logger or None = None
) -> pd.DataFrame:
    """ Function dedicated to loading requests """
    df = False
    ext_type_n = None
    for ext_type_n, ext_func in enumerate([pd.read_csv, pd.read_excel, pd.read_parquet]):
        try:
            df = ext_func(path)
        except FileNotFoundError or pyarrow.lib.ArrowInvalid:
            pass
        else:
            break

    optional_log(30, "Demand read", logger)

    if all(col_name in df.columns for col_name in
            ['origin_long', 'origin_y', 'destination_long', 'destination_y'])\
            and not all(col_name in df.columns for col_name in ['origin', 'destination']):
        optional_log(30, "Demand structured with non-osmnx, writing new columns..", logger)
        city_graph = nx.read_graphml(config['paths']['city_graph'])
        for org_dest in ['origin', 'destination']:
            df[org_dest] = df.apply(
                lambda row: ox.nearest_nodes(city_graph, row[org_dest+'_long'], row[org_dest+'_lat']),
                axis=1
            )
            df[org_dest] = df.apply(lambda row: row[0] if isinstance(row, list) else int(row), axis=1)
        if ext_type_n == 0:
            df.to_csv(path)
        elif ext_type_n == 1:
            df.to_excel(path)
        elif ext_type_n == 2:
            df.to_parquet(path)
        else:
            raise SystemExit("Incorrect format")

    return df
