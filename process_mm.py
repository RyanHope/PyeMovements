#!/usr/bin/env python

import sys, os
from tables import *

class CRISP(IsDescription):
    timer_states = UInt16Col()
    timer_mean1  = Float32Col()
    timer_mean2  = Float32Col()
    timer_mean3  = Float32Col()
    labile_mean  = Float32Col()
    labile_stdev = Float32Col()
    cue_cancel_prob  = Float32Col()
    latencies  = UInt16Col(2500)

if __name__ == '__main__':
	
    if len(sys.argv) != 3:
        print "Usage: process_mm.py [RESULT_FILE] [JOB_sNAME]"
        sys.exit(-1)
    
    fin = open(sys.argv[1], "r")
    base = os.path.splitext(sys.argv[1])[0]
    header = fin.readline().strip().split("\t")
    
    h5file = open_file("%s.h5" % base, mode = "w", title = sys.argv[2])
    points = h5file.create_group("/", 'points', 'FullMeshSpace')
    table = h5file.create_table(points, 'latencies', CRISP, "Antisacade First Saccade Latencies with Gap & Cue Cancellation")
    crisp = table.row
    for line in fin:
        line = line.strip().split("\t")[:-1]
        if len(line) == 8:
			latencies = line[-1].split("|")
			if len(latencies) == 2500:
				crisp["timer_states"] = line[0]
				crisp["timer_mean1"] = line[1]
				crisp["timer_mean2"] = line[2]
				crisp["timer_mean3"] = line[3]
				crisp["labile_mean"] = line[4]
				crisp["labile_stdev"] = line[5]
				crisp["cue_cancel_prob"] = line[6]
				crisp["latencies"] = latencies
				crisp.append()
			else:
				print line[0:7]
        else:
            print line
    
    table.flush()
    h5file.close()
    fin.close()
