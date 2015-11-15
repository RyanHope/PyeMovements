#!/usr/bin/env python

import sys,os
import itertools
import types
import simpy
import numpy as np
import struct

from crisp import *

class AntiSaccadeTask(object):

	def __init__(self, env):
		self.env = env
		self.trial = 0
		self.states = ["FIXATE","GAP","CUE","TARGET","MASK"]
		self.modes = ["anti","pro"]
		self.sides = ["left","right"]
		self.reset()
		self.process = env.process(self.run())

	def reset(self):
		self.trial += 1
		self.fixate_dur = np.random.uniform(1.5,3.5)
		self.mode = self.modes[np.random.randint(2)]
		self.cue_side = self.sides[np.random.randint(2)]
		self.gap_dur = .2
		self.cue_dur = .4
		self.target_dur = .15
		self.state = 0
		self.cue_time = 0

	def respond(self, answer):
		self.process.interrupt()
		self.reset()

	def run(self):
		while True:
			try:
				self.env.log(-1, "ast", self.states[self.state])
				if self.state == 0: # FIXATE
					yield self.env.timeout(self.fixate_dur)
				elif self.state == 1: # GAP
					yield self.env.timeout(self.gap_dur)
				elif self.state == 2: # CUE
					self.cue_time = self.env.now
					yield self.env.timeout(self.cue_dur)
				elif self.state == 3: # TARGET
					yield self.env.timeout(self.target_dur)
				elif self.state == 4: # MASK
					yield self.env.timeout(simpy.core.Infinity)
			except simpy.Interrupt as e:
				pass
			if self.state < len(self.states):
				self.state += 1

def main(args):
	env = CRISPEnvironment(args)

	# Create components
	processVision = ProcessVision(env)
	saccadeExec = SaccadeExec(env, processVision, mean=args['exec_mean'])
	nonLabileProg = NonLabileProg(env, saccadeExec, mean=args['nonlabile_mean'])
	labileProg = LabileProg(env, nonLabileProg, mean=args['labile_mean'])
	timer = Timer(env, labileProg, mean=args['timer_mean1'], states=args['timer_states'], start_state=args['timer_start_state'])

	ast = AntiSaccadeTask(env)
	#f = open("latencies-%d-%.2f-%.2f-%.2f-%.2f.txt" % (args["max_trials"],args["timer_mean"],args["labile_mean"],args["gap_cancel_prob"],args["cue_cancel_prob"]),"w")
	latencies = []
	def endCond(e):
		ret = False
		if e[2]=="ast" and e[3]=="GAP":
			timer.setMean(args['timer_mean2'])
			if np.random.uniform() < args["gap_cancel_prob"]:
				labileProg.process.interrupt(-1)
		if e[2]=="ast" and e[3]=="CUE":
			timer.setMean(args['timer_mean3'])
			if np.random.uniform() < args["cue_cancel_prob"]:
				labileProg.process.interrupt(-1)
		if ast.state>1 and (e[2]=="saccade_execution" and e[3]=="started"):
			latencies.append(float(env.now-ast.cue_time))
			#f.write("%d\t%f\t%f\t%f\t%f\t%f\n" % (args["max_trials"],args["timer_mean"],args["labile_mean"],args["gap_cancel_prob"],args["cue_cancel_prob"],float(env.now-ast.cue_time)))
			#f.flush()
			if ast.trial == args["max_trials"]:
				ret = True
			else:
				ast.respond(None)
		return ret

	env.debug = True
	env.run_while(endCond)
	#f.close()
	return {
		# "max_trials": args["max_trials"],
		# "timer_mean": args["timer_mean"],
		# "labile_mean": args["labile_mean"],
		# "gap_cancel_prob": args["gap_cancel_prob"],
		# "cue_cancel_prob": args["cue_cancel_prob"],
		"latencies": "|".join(map(lambda x: str(int(np.round_(x,3)*1000)), latencies))
	}

def get_args(args=sys.argv[1:]):
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--max-trials", type=int, default=1)
	parser.add_argument("--timer_mean1", type=float, action="store", default=0.250)
	parser.add_argument("--timer_mean2", type=float, action="store", default=0.250)
	parser.add_argument("--timer_mean3", type=float, action="store", default=0.250)
	parser.add_argument("--timer_states", type=int, default=11)
	parser.add_argument("--timer_start_state", type=int, default=-1)
	parser.add_argument("--labile_mean", type=float, action="store", default=.180)
	parser.add_argument("--labile_stdev", type=float, action="store", default=.060)
	parser.add_argument("--nonlabile_mean", type=float, action="store", default=.040)
	parser.add_argument("--nonlabile_stdev", type=float, action="store", default=.010)
	parser.add_argument("--exec_mean", type=float, action="store", default=.040)
	parser.add_argument("--exec_stdev", type=float, action="store", default=.010)
	parser.add_argument("--gap_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--cue_cancel_prob", type=float, action="store", default=0.00)
	return vars(parser.parse_args(args))

def run_mm(timer_states, timer_mean1, timer_mean2, timer_mean3, labile_mean, labile_stdev, cue_cancel_prob):
	args = get_args([])
	args["timer_states"] = float(timer_states)
	args["timer_mean1"] = float(timer_mean1)
	args["timer_mean2"] = float(timer_mean2)
	args["timer_mean3"] = float(timer_mean3)
	args["labile_mean"] = float(labile_mean)
	args["labile_stdev"] = float(labile_stdev)
	args["cue_cancel_prob"] = float(cue_cancel_prob)
	return main(args)

if __name__ == '__main__':
	print main(get_args())
