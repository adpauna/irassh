import pickle
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input_file", help="input text file")
parser.add_argument("output_file",
                    help="output filename (will be a pickle file containing a list of strings that represent the lines of the input file")

args = parser.parse_args()

with open(args.input_file, "r") as f:
    lines = f.readlines()

i = 0
while i<(len(lines)-1):
    lines[i] = lines[i][:-1]
    i+=1

with open(args.output_file, "wb") as f:
    pickle.dump(lines,f)