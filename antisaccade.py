#!/usr/bin/env python

import sys,os
import itertools
import types
import simpy
import numpy as np
import struct
import json

from crisp import *

class AntiSaccadeTask(object):

	def __init__(self, env):
		self.env = env
		self.trial = 0
		self.states = ["FIXATE","GAP","CUE","TARGET","MASK"]
		self.modes = ["anti","pro"]
		self.sides = [-1,1]
		self.reset()
		self.process = env.process(self.run())

	def reset(self):
		self.trial += 1
		self.fixate_dur = np.random.uniform(0.5,1.5)
		self.mode = "pro"#self.modes[np.random.randint(2)]
		self.cue_side = self.sides[np.random.randint(2)]
		self.target_side = -1
		if self.mode == "pro" and self.cue_side == "right":
			self.target_side = 1
		elif self.mode == "anti" and self.cue_side == "left":
			self.target_side = 1
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

class ASTLabileProg(LabileProg):

	def getTarget(self, alpha=0):
		if alpha > np.random.uniform():
			# top-down
			pass
		else:
			# bottom-up
			if self.env.ast.state < 2:
				self.target = 0
			elif self.env.ast.state == 2:
				self.target = self.env.ast.cue_side
			elif self.env.ast.state > 2:
				self.target = self.env.ast.target_side

def main(args):
	env = CRISPEnvironment(args)

	# Create task components
	env.ast = AntiSaccadeTask(env)

	# Create model components
	processVision = ProcessVision(env)
	saccadeExec = SaccadeExec(env, processVision, mean=args['exec_mean'])
	nonLabileProg = NonLabileProg(env, saccadeExec, mean=args['nonlabile_mean'])
	labileProg = ASTLabileProg(env, nonLabileProg, mean=args['labile_mean'])
	timer = Timer(env, labileProg, mean=args['timer_mean'], states=args['timer_states'], start_state=args['timer_start_state'])

	latencies = []
	def endCond(e):
		ret = False
		if e[2]=="ast" and e[3]=="GAP":
			timer.setRate(args['gap_timer_rate'])
			if np.random.uniform() < args["gap_cancel_prob"]:
				labileProg.process.interrupt(-1)
		if e[2]=="ast" and e[3]=="CUE":
			timer.setRate(args['cue_timer_rate'])
			if np.random.uniform() < args["cue_cancel_prob"]:
				labileProg.process.interrupt(-1)
		if e[2]=="ast" and e[3]=="TARGET":
			timer.setRate(args['target_timer_rate'])
			if np.random.uniform() < args["target_cancel_prob"]:
				labileProg.process.interrupt(-1)
		if env.ast.state>1 and (e[2]=="saccade_execution" and e[3]=="started" and e[6]!=0):
			latencies.append(float(env.now-env.ast.cue_time))
			if env.ast.trial == args["max_trials"]:
				ret = True
			else:
				env.ast.respond(None)
		return ret

	env.debug = args["debug"]
	env.run_while(endCond)
	return {
		"latencies": "|".join(map(lambda x: str(int(np.round_(x,3)*1000)), latencies))
	}

def get_args(args=sys.argv[1:]):
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--max-trials", type=int, default=2500)
	parser.add_argument("--timer_mean", type=float, action="store", default=0.250)
	parser.add_argument("--timer_states", type=int, default=11)
	parser.add_argument("--timer_start_state", type=int, default=-1)
	parser.add_argument("--labile_mean", type=float, action="store", default=.180)
	parser.add_argument("--labile_stdev", type=float, action="store", default=.060)
	parser.add_argument("--nonlabile_mean", type=float, action="store", default=.040)
	parser.add_argument("--nonlabile_stdev", type=float, action="store", default=.010)
	parser.add_argument("--exec_mean", type=float, action="store", default=.040)
	parser.add_argument("--exec_stdev", type=float, action="store", default=.010)
	parser.add_argument("--gap_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--gap_timer_rate", type=float, action="store", default=1.0)
	parser.add_argument("--cue_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--cue_timer_rate", type=float, action="store", default=1.0)
	parser.add_argument("--target_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--target_timer_rate", type=float, action="store", default=1.0)
	parser.add_argument("--debug", action="store_true")
	parser.add_argument('--outfile', type=argparse.FileType('w'), default=-1, nargs="?")
	return vars(parser.parse_args(args))

def run_mm(timer_states, timer_mean, labile_mean, labile_stdev, gap_cancel_prob, gap_timer_rate, cue_cancel_prob, cue_timer_rate):
	args = get_args([])
	args["timer_states"] = float(timer_states)
	args["timer_mean"] = float(timer_mean)
	args["labile_mean"] = float(labile_mean)
	args["labile_stdev"] = float(labile_stdev)
	args["gap_cancel_prob"] = float(gap_cancel_prob)
	args["gap_timer_rate"] = float(gap_timer_rate)
	args["cue_cancel_prob"] = float(cue_cancel_prob)
	args["cue_timer_rate"] = float(cue_timer_rate)
	return main(args)

if __name__ == '__main__':
	args = get_args()
	results = main(args)
	if args["outfile"] != -1:
		if args["outfile"] == None:
			json.dump(results, sys.stdout)
		else:
			json.dump(results, args["outfile"])
