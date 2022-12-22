import pickle
import argparse
import pprint
import json

parser = argparse.ArgumentParser()
parser.add_argument("input_file", help="input pickle file")
parser.add_argument("output_file",
                    help="output filename (will be a text file")

args = parser.parse_args()

with open(args.input_file, "r") as f:
    obj = f.read()#.replace('\n', '')

with open(args.output_file, "wb") as f:
    pprint.pprint(pickle.loads(obj))
    f.write(json.dumps(pickle.loads(obj), indent=2) + '\n')
    f.close()