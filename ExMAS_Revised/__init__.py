import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--requests-csv", type=str, required=True)
parser.add_argument("--parameters-json", type=str, required=True)
args = parser.parse_args()



