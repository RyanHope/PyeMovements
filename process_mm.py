#!/usr/bin/env python

import sys, os
from tables import *

class CRISP(IsDescription):
    timer_mean  = Float32Col()
    labile_mean  = Float32Col()
    gap_cancel_prob  = Float32Col()
    cue_cancel_prob  = Float32Col()
    latencies  = UInt16Col(5000)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: process_mm.py [RESULT_FILE] [JOB_NAME]"
        sys.exit(-1)
    fin = open(sys.argv[1], "r")
    base = os.path.splitext(sys.argv[1])[0]
    header = fin.readline().strip().split("\t")#[:-2] + ["latency"]
    h5file = open_file("%s.h5" % base, mode = "w", title = sys.argv[2])
    points = h5file.create_group("/", 'points', 'FullMeshSpace')
    table = h5file.create_table(points, 'latencies', CRISP, "Antisacade First Saccade Latencies with Gap & Cue Cancellation")
    crisp = table.row
    for line in fin:
        line = line.strip().split("\t")[:-1]
        if len(line) == 6:
            crisp["timer_mean"] = line[1]
            crisp["labile_mean"] = line[2]
            crisp["gap_cancel_prob"] = line[3]
            crisp["cue_cancel_prob"] = line[4]
            crisp["latencies"] = line[-1].split("|")
            crisp.append()
        else:
            print line
    table.flush()
    h5file.close()
    fin.close()
