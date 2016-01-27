#!/usr/bin/env python

import sys, os
from tables import *

class CRISP(IsDescription):
    sid = StringCol(5)
    timer_states = UInt16Col()
    timer_mean  = Float32Col()
    labile_mean  = Float32Col()
    labile_stdev = Float32Col()
    attn_mean  = Float32Col()
    attn_stdev = Float32Col()
    cue_cancel_prob  = Float32Col()
    gap_cancel_prob  = Float32Col()
    cue_timer_rate  = Float32Col()
    gap_timer_rate  = Float32Col()
    alpha  = Float32Col()
    lat_mean = Float32Col()
    lat_std = Float32Col()


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print "Usage: process_mm.py [RESULT_FILE] [JOB_NAME]"
        sys.exit(-1)

    sids = ["0304b","06fbf","1f330","31fc9","3d5bd","427fc","49c3b","547cb",
            "57548","6de95","7a44c","8b747","a314d","a9e6e","b422c","b4a6f",
            "b608f","bd801","c39a8","d17cc","d4912","e1070","e35da"]
    stat = ["mean","std"]
    measure = "lat"
    mode = "pro"

    fin = open(sys.argv[1], "r")
    base = os.path.splitext(sys.argv[1])[0]
    header = fin.readline().strip().split("\t")
    N = len(header)

    h5file = open_file("%s_%s_%s.h5" % (base,mode,measure), mode = "w", title = sys.argv[2])
    points = h5file.create_group("/", 'points', 'FullMeshSpace')
    table = h5file.create_table(points, 'latencies', CRISP, "Antisacade First Saccade Latencies with Gap & Cue Cancellation")

    crisp = table.row
    for line in fin:
        line = line.strip().split("\t")
        data = {}
        for c in range(11,N-1):
            data[header[c]] = line[c]
        for sid in sids:
            crisp["sid"] = sid
            crisp["timer_states"] = line[0]
            crisp["timer_mean"] = line[1]
            crisp["labile_mean"] = line[2]
            crisp["labile_stdev"] = line[3]
            crisp["attn_mean"] = line[4]
            crisp["attn_stdev"] = line[5]
            crisp["gap_cancel_prob"] = line[6]
            crisp["gap_timer_rate"] = line[7]
            crisp["cue_cancel_prob"] = line[8]
            crisp["cue_timer_rate"] = line[9]
            crisp["alpha"] = line[10]
            crisp["lat_mean"] = data["pro_lat_mean_%s" % sid]
            crisp["lat_std"] = data["pro_lat_std_%s" % sid]
            crisp.append()

    table.flush()
    h5file.close()
    fin.close()
