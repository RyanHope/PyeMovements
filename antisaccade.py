#!/usr/bin/env python

import sys,os
import itertools
import types
import simpy
import numpy as np

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
	timer = Timer(env, labileProg, mean=args['timer_mean'], states=args['timer_states'], start_state=args['timer_start_state'])

	ast = AntiSaccadeTask(env)
	#f = open("latencies-%d-%.2f-%.2f-%.2f-%.2f.txt" % (args["max_trials"],args["timer_mean"],args["labile_mean"],args["gap_cancel_prob"],args["cue_cancel_prob"]),"w")
	latencies = []
	def endCond(e):
		ret = False
		if e[2]=="ast" and e[3]=="GAP":
			if np.random.uniform() < args["gap_cancel_prob"]:
				labileProg.process.interrupt(-1)
		if e[2]=="ast" and e[3]=="CUE":
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

	env.debug = False
	env.run_while(endCond)
	#f.close()
	return {
		# "max_trials": args["max_trials"],
		# "timer_mean": args["timer_mean"],
		# "labile_mean": args["labile_mean"],
		# "gap_cancel_prob": args["gap_cancel_prob"],
		# "cue_cancel_prob": args["cue_cancel_prob"],
		"latencies": latencies
	}

def get_args(args=sys.argv[1:]):
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--max-trials", type=int, default=1,
						help="the number of complete saccades to generate")
	parser.add_argument("--timer_mean", type=float, action="store", default=0.250,
						help="the average timer interval in ms")
	parser.add_argument("--timer_states", type=int, default=11,
						help="the number of discrete states in the random walk timer")
	parser.add_argument("--timer_start_state", type=int, default=-1,
						help="the starting state of the random walk timer")
	parser.add_argument("--labile_mean", type=float, action="store", default=.180,
						help="the average timer interval in ms")
	parser.add_argument("--nonlabile_mean", type=float, action="store", default=0.040,
						help="the average timer interval in ms")
	parser.add_argument("--exec_mean", type=float, action="store", default=.04,
						help="the average timer interval in ms")
	parser.add_argument("--gap_cancel_prob", type=float, action="store", default=0.00,
						help="the probability of cancelation on gap")
	parser.add_argument("--cue_cancel_prob", type=float, action="store", default=0.00,
	          help="the probability of cancelation on cue")
	return vars(parser.parse_args(args))

def run_mm(max_trials, timer_mean, labile_mean, gap_cancel_prob, cue_cancel_prob):
	args = get_args([])
	args["max_trials"] = int(max_trials)
	args["timer_mean"] = float(timer_mean)
	args["labile_mean"] = float(labile_mean)
	args["gap_cancel_prob"] = float(gap_cancel_prob)
	args["cue_cancel_prob"] = float(cue_cancel_prob)
	return main(args)

if __name__ == '__main__':
	import json
	print(json.dumps(main(get_args())))
