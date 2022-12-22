import pickle
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("input_file", help="input text file")
parser.add_argument("output_file",
                    help="output filename (will be a pickle file containing a list of strings that represent the lines of the input file")

args = parser.parse_args()

with open(args.input_file, "r") as f:
#    lines = f.readlines()
    data = json.load(f)

with open(args.output_file, "wb") as f:
    pickle.dump(data,f)