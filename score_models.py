#!/usr/bin/env python

import sys, os

from scipy.stats import ks_2samp

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print "Usage: process_mm.py [RESULT_FILE]"
        sys.exit(-1)

    with open("scores.txt","w") as scores:
        with open(sys.argv[1], "r") as fin:
            header = fin.readline().strip().split("\t")
            with open("latencies.csv","r") as data:
                subjects = {}
                for line in data.readlines():
                    line = line.strip().split(",")
                    lat = [float(l) for l in line[1:]]
                    subjects[line[0]] = lat
                with open("scores.csv","w") as o:
                    for line in fin:
                        line = line.strip().split("\t")[:-1]
                        if len(line) == 8:
                            latencies = [float(l)/1000 for l in line[-1].split("|")]
                            for s in subjects.keys():
                                d,p = ks_2samp(subjects[s],latencies)
                                scores.write(s+"\t"+"\t".join(line[:-1]) + "\t%.3f\t%.3f" % (d,p) + "\n")
                                scores.flush()
