import pickle
import argparse
import json
import fileinput
import re


# simple script that will assign number codes to commands in a sequential way

parser = argparse.ArgumentParser()
parser.add_argument("input_file", help="input text file")
parser.add_argument("output_file",
                    help="substitutes command codes in a sequential way")

args = parser.parse_args()

fin = open(args.input_file, "rt")
fout = open(args.output_file, "wt")


pattern = re.compile(r"\d+[\,]")
i = 0
for line in fin:
    #print('line')
    #print(line)
    
    if re.search(pattern, line) is not None:
        print('match')
        print(line)
        print('i: ' + str(i))
        print('new pattern')
        print(pattern.sub(lambda m: str(i) + ',', line))
        fout.write(pattern.sub(lambda m: str(i) + ',', line))
        i = i + 1
    else:
        fout.write(line)
        
    
fin.close()
fout.close()