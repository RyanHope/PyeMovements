#!/usr/bin/env python

import sys

if __name__ == '__main__':
    fin = open(sys.argv[1], "r")
    header = fin.readline().strip().split("\t")[:-2] + ["latency"]
    fout = open("%s.melted" % sys.argv[1], "w")
    fout.write("\t".join(header))
    fout.write("\n")
    fout.flush()
    for line in fin:
        line = line.strip().split("\t")[:-1]
        for l in line[-1].split("|"):
            fout.write("\t".join(line[:-1]+[l]))
            fout.write("\n")
        fout.flush()
    fin.close()
    fout.close()
