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

	def __init__(self, env, mode):
		self.env = env
		self.trial = 0
		self.states = ["FIXATE","GAP","CUE","TARGET","MASK"]
		self.mode = mode
		self.sides = [-1,1]
		self.reset()
		self.process = env.process(self.run())

	def reset(self):
		self.trial += 1
		self.fixate_dur = np.random.uniform(0.5,1.5)
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

	def getTarget(self):
		if self.alpha < 0: # negative alpha means no spatial
			self.target = 1 - np.random.sample(1)[0]
			if np.random.sample(1) < .5:
				self.target = -1 * self.target # abs(self.target) should always be > 0
		else:
			td_target = self.attn.position
			if self.env.ast.state < 2:
				bu_target = 0
			elif self.env.ast.state == 2:
				bu_target = self.env.ast.cue_side
			elif self.env.ast.state > 2:
				bu_target = self.env.ast.target_side
			self.target = self.alpha * td_target + (1-self.alpha) * bu_target

class VisualAttention(object):
	__alias__ = "attention_shift"
	def __init__(self, env, mean=.180, stdev=3):
		self.env = env
		self.setMean(mean)
		self.setStdev(stdev)
		self.target = 0
		self.position = 0
		self.next_event = 0
		self.process = env.process(self.run())
		self.restarts = 0
		self.target = 0
		self.position = 0

	def setMean(self, mean):
		self.mean = mean
		self.env.log(0, self.__alias__, "set_mean", self.mean)

	def setStdev(self, stdev):
		self.stdev = self.mean/stdev
		self.env.log(0, self.__alias__, "set_stdev", self.stdev)

	def run(self):
		while True:
			if self.next_event == 0:
				self.next_event = simpy.core.Infinity
			while self.next_event:
				try:
					self.event = self.env.timeout(self.next_event, self.target)
					yield self.event
					self.next_event = 0
				except simpy.Interrupt as e:
					if self.next_event < simpy.core.Infinity:
						self.env.log(-1, self.__alias__, "restarted")
						self.restarts += 1
					self.target = e.cause
					self.next_event = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
													  (self.stdev*self.stdev)/self.mean)
					self.env.log(-1, self.__alias__, "started", self.target)
			self.env.log(-1, self.__alias__, "complete", self.target)
			self.position = self.event.value
			self.restarts = 0

def main(args):
	lat_data_pro = "latencies_pro.csv"
	lat_data_anti = "latencies_anti.csv"
	amp_data_pro = "amplitudes_pro.csv"
	amp_data_anti = "amplitudes_anti.csv"
	data_all = {}

	with open(lat_data_pro,"r") as data:
		for line in data.readlines():
			line = line.strip().split(",")
			lat = [float(l) for l in line[1:]]
			data_all[line[0]] = {}
			data_all[line[0]]["pro"] = {}
			data_all[line[0]]["pro"]["lat"] = lat
	with open(lat_data_anti,"r") as data:
		for line in data.readlines():
			line = line.strip().split(",")
			lat = [float(l) for l in line[1:]]
			data_all[line[0]]["anti"] = {}
			data_all[line[0]]["anti"]["lat"] = lat
	with open(amp_data_pro,"r") as data:
		for line in data.readlines():
			line = line.strip().split(",")
			amp = [float(a) for a in line[1:]]
			data_all[line[0]]["pro"]["amp"] = amp
	with open(amp_data_anti,"r") as data:
		for line in data.readlines():
			line = line.strip().split(",")
			amp = [float(a) for a in line[1:]]
			data_all[line[0]]["anti"]["amp"] = amp
	
	from scipy.stats import ks_2samp

	latenciesb = []
	amplitudesb = []
	for b in xrange(args["batches"]):
		for mode in ["pro","anti"]:
			latencies = []
			amplitudes = []
			for t in xrange(args["max_trials"]):
				env = CRISPEnvironment(args)

				# Create task components
				env.ast = AntiSaccadeTask(env, mode)

				# Create model components
				processVision = ProcessVision(env)
				visAttn = None
				if args["alpha"] >= 0:
					visAttn = VisualAttention(env, mean=args['attn_mean'], stdev=args['attn_stdev'])
				saccadeExec = SaccadeExec(env, processVision, mean=args['exec_mean'], stdev=args['exec_stdev'])
				nonLabileProg = NonLabileProg(env, saccadeExec, mean=args['nonlabile_mean'], stdev=args['nonlabile_stdev'])
				labileProg = ASTLabileProg(env, nonLabileProg, visAttn, mean=args['labile_mean'], stdev=args['labile_stdev'], alpha=args['alpha'])
				timer = Timer(env, labileProg, mean=args['timer_mean'], states=args['timer_states'], start_state=args['timer_start_state'])

				def endCond(e):
					ret = False
					if e[2]=="ast" and e[3]=="GAP":
						timer.setRate(args['gap_timer_rate'])
						if args["alpha"] >= 0:
							visAttn.process.interrupt(0)
						if np.random.uniform() < args["gap_cancel_prob"]:
							labileProg.process.interrupt(-1)
					if e[2]=="ast" and e[3]=="CUE":
						timer.setRate(args['cue_timer_rate'])
						if args["alpha"] >= 0:
							visAttn.process.interrupt(env.ast.target_side)
						if np.random.uniform() < args["cue_cancel_prob"]:
							labileProg.process.interrupt(-1)
					if e[2]=="ast" and e[3]=="TARGET":
						timer.setRate(args['target_timer_rate'])
						if args["alpha"] >= 0:
							visAttn.process.interrupt(env.ast.target_side)
						if np.random.uniform() < args["target_cancel_prob"]:
							labileProg.process.interrupt(-1)
					if env.ast.state>1 and (e[2]=="saccade_execution" and e[3]=="started" and abs(e[6])>0):
						latencies.append(float(env.now-env.ast.cue_time))
						amplitudes.append(float(e[6]))
						ret = True
					return ret

				env.debug = args["debug"]
				env.run_while(endCond)

			latenciesb.append(latencies)
			amplitudesb.append(amplitudes)

	results = {}
	for sid in data_all.keys():
		for mode in ["pro","anti"]:
			ks_scores_lat = []
			ks_scores_amp = []
			for lb in latenciesb:
				ks,_ = ks_2samp(lb,data_all[sid][mode]["lat"])
				ks_scores_lat.append(ks)
			for ab in amplitudesb:
				ks,_ = ks_2samp(ab,data_all[sid][mode]["amp"])
				ks_scores_amp.append(ks)
			results["%s_lat_mean_%s" % (mode,sid)] = round(np.mean(ks_scores_lat),3)
			results["%s_lat_std_%s" % (mode,sid)] = round(np.std(ks_scores_lat),3)
			results["%s_amp_mean_%s" % (mode,sid)] = round(np.mean(ks_scores_amp),3)
			results["%s_amp_std_%s" % (mode,sid)] = round(np.std(ks_scores_amp),3)
	return results

def get_args(args=sys.argv[1:]):
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--max-trials", type=int, default=250)
	parser.add_argument("--batches", type=int, default=20)
	parser.add_argument("--timer_mean", type=float, action="store", default=0.250)
	parser.add_argument("--timer_states", type=int, default=11)
	parser.add_argument("--timer_start_state", type=int, default=-1)
	parser.add_argument("--labile_mean", type=float, action="store", default=.180)
	parser.add_argument("--labile_stdev", type=int, action="store", default=7)
	parser.add_argument("--nonlabile_mean", type=float, action="store", default=.040)
	parser.add_argument("--nonlabile_stdev", type=int, action="store", default=7)
	parser.add_argument("--exec_mean", type=float, action="store", default=.040)
	parser.add_argument("--exec_stdev", type=int, action="store", default=7)
	parser.add_argument("--attn_mean", type=float, action="store", default=.180)
	parser.add_argument("--attn_stdev", type=int, action="store", default=7)
	parser.add_argument("--gap_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--gap_timer_rate", type=float, action="store", default=1.0)
	parser.add_argument("--cue_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--cue_timer_rate", type=float, action="store", default=1.0)
	parser.add_argument("--target_cancel_prob", type=float, action="store", default=0.00)
	parser.add_argument("--target_timer_rate", type=float, action="store", default=1.0)
	parser.add_argument("--alpha", type=float, action="store", default=0.5)
	parser.add_argument("--debug", action="store_true")
	parser.add_argument('--outfile', type=argparse.FileType('w'), default=-1, nargs="?")
	return vars(parser.parse_args(args))

def run_mm(timer_states, timer_mean, labile_mean, labile_stdev, attn_mean, attn_stdev, gap_cancel_prob, gap_timer_rate, cue_cancel_prob, cue_timer_rate, alpha):
	args = get_args([])
	args["timer_states"] = float(timer_states)
	args["timer_mean"] = float(timer_mean)
	args["labile_mean"] = float(labile_mean)
	args["labile_stdev"] = float(labile_stdev)
	args["attn_mean"] = float(attn_mean)
	args["attn_stdev"] = float(attn_stdev)
	args["gap_cancel_prob"] = float(gap_cancel_prob)
	args["gap_timer_rate"] = float(gap_timer_rate)
	args["cue_cancel_prob"] = float(cue_cancel_prob)
	args["cue_timer_rate"] = float(cue_timer_rate)
	args["alpha"] = float(alpha)
	return main(args)

if __name__ == '__main__':
	args = get_args()
	results = main(args)
	if args["outfile"] != -1:
		if args["outfile"] == None:
			json.dump(results, sys.stdout)
		else:
			json.dump(results, args["outfile"])
	sys.stdout.flush()
