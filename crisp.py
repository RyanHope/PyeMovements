#!/usr/bin/env python2

import sys,os
import itertools
import types
import simpy
import numpy as np

class BrainstemOscillator(object):
	def __init__(self, env, sp, mean=.250, states=11, start_state=0):
		self.env = env
		self.sp = sp
		self.mean = mean
		self.states = states
		self.start_state = start_state if start_state < self.states else self.states-1
		self.process = env.process(self.run())

	def next_state(self):
		yield self.env.timeout(-(self.mean / self.states) * np.log(1 - np.random.uniform()))

	def run(self):
		for i in itertools.count():
			for j in itertools.count(self.start_state):
				if j < self.states:
					yield self.env.process(self.next_state())
				else:
					break
			self.sp.process.interrupt()

class SaccadePlanner(object):

	def __init__(self, env, sp, mean=.180):
		self.env = env
		self.sp = sp
		self.mean = mean
		self.stdev = mean/4.0
		self.next_saccade = 0
		self.saccade_id = 0
		self.process = env.process(self.run())

	def new_saccade(self):
		self.next_saccade = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
											(self.stdev*self.stdev)/self.mean)
		self.saccade_id += 1
		self.env.log(self.saccade_id, "target_selection", "started")

	def run(self):
		while True:
			if self.next_saccade == 0:
				self.next_saccade = simpy.core.Infinity
			while self.next_saccade:
				try:
					yield self.env.timeout(self.next_saccade)
					self.next_saccade = 0
				except simpy.Interrupt as e:
					if self.next_saccade < simpy.core.Infinity:
						self.env.log(self.saccade_id, "target_selection", "canceled")
					self.new_saccade()
			self.sp.saccade_id = self.saccade_id
			self.sp.process.interrupt()
			self.env.log(self.saccade_id, "target_selection", "complete")

class SaccadeProgrammer(object):

	def __init__(self, env, sp, mean=.040):
		self.env = env
		self.sp = sp
		self.mean = mean
		self.stdev = mean/4.0
		self.ex_saccade = 0
		self.saccade_id = 0
		self.process = env.process(self.run())

	def _ex_saccade(self):
		self.ex_saccade = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
										  (self.stdev*self.stdev)/self.mean)
		self.env.log(self.saccade_id, "programming", "started")

	def run(self):
		while True:
			if self.ex_saccade == 0:
				self.ex_saccade = simpy.core.Infinity
			while self.ex_saccade:
				try:
					yield self.env.timeout(self.ex_saccade)
					self.ex_saccade = 0
				except simpy.Interrupt as e:
					if self.ex_saccade < simpy.core.Infinity:
						raise RuntimeError("programming canceled")
						self.env.log(self.saccade_id, "programming" "canceled")
					self._ex_saccade()
			self.sp.saccade_id = self.saccade_id
			self.sp.process.interrupt()
			self.env.log(self.saccade_id, "programming", "complete")

class SaccadeExec(object):

	def __init__(self, env, mean=.040):
		self.env = env
		self.mean = mean
		self.stdev = mean/3.0
		self.ex_saccade = 0
		self.saccade_id = 0
		self.process = env.process(self.run())

	def _ex_saccade(self):
		self.ex_saccade = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
										  (self.stdev*self.stdev)/self.mean)
		if self.env.active_saccades == 0:
			self.env.saccade_id += 1
		self.env.active_saccades += 1
		self.env.log(self.saccade_id, "execution", "started")
		self.env.fixation_durations.append(self.env.now-self.env.fixation_start)

	def run(self):
		while True:
			if self.ex_saccade == 0:
				self.ex_saccade = simpy.core.Infinity
			while self.ex_saccade:
				try:
					yield self.env.timeout(self.ex_saccade)
					self.ex_saccade = 0
				except simpy.Interrupt as e:
					if self.ex_saccade < simpy.core.Infinity:
						self.env.log(self.saccade_id, "execution", "merged")
					self._ex_saccade()
			self.env.fixation_id += 1
			self.env.log(self.saccade_id, "execution","complete")
			self.env.active_saccades -= 1
			self.env.fixation_start = self.env.now

class LoggingEnvironment(simpy.Environment):

	def __init__(self, args, output=sys.__stdout__, initial_time=0):
		super(LoggingEnvironment, self).__init__(initial_time)
		self.active_saccades = 0
		self.saccade_id = 0
		self.cancellations = 0
		self.fixation_id = 1
		self.fixation_start = 0
		self.fixation_durations = []
		if output!=sys.__stdout__:
			self.out = open(os.path.abspath(output))
		else:
			self.out = output
		self.out.write("# %s\n" % args)
		self.out.write("time\tactive_saccades\tcancellations\tsaccade_id\tfixation_id\tprogram_id\tstage\tstatus\n")

	def log(self, id, stage, status):
		sac_id = self.saccade_id if self.active_saccades>0 else 0
		fix_id = self.fixation_id if self.active_saccades==0 else 0
		if stage=="execution":
			fix_id = self.fixation_id
		elif stage=="target_selection":
			if status=="canceled":
				self.cancellations += 1
			elif status=="complete":
				self.cancellations = 0
		self.out.write("%f\t%d\t%d\t%d\t%d\tsaccade-%d\t%s\t%s\n" % (self.now, self.active_saccades, self.cancellations, sac_id, fix_id, id, stage, status))
		self.out.flush()

if __name__ == '__main__':

	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--max-saccades", type=int, default=1,
						help="the number of complete saccades to generate")
	parser.add_argument("--timer_mean", type=float, action="store", default=.250,
						help="the average timer interval in ms")
	parser.add_argument("--timer_states", type=int, default=11,
						help="the number of discrete states in the random walk timer")
	parser.add_argument("--timer_start_state", type=int, default=0,
						help="the starting state of the random walk timer")
	parser.add_argument("--labile_mean", type=float, action="store", default=.180,
						help="the average timer interval in ms")
	parser.add_argument("--nonlabile_mean", type=float, action="store", default=.04,
						help="the average timer interval in ms")
	parser.add_argument("--exec_mean", type=float, action="store", default=.04,
						help="the average timer interval in ms")
	args = vars(parser.parse_args())

	env = LoggingEnvironment(args)

	# Create components
	saccade_exec = SaccadeExec(env, mean=args['exec_mean'])
	saccade_programmer = SaccadeProgrammer(env, saccade_exec, mean=args['nonlabile_mean'])
	saccade_planner = SaccadePlanner(env, saccade_programmer, mean=args['labile_mean'])
	brainstem_oscillator = BrainstemOscillator(env, saccade_planner, mean=args['timer_mean'],
											   states=args['timer_states'],
											   start_state=args['timer_start_state'])

	# Run
	while env.saccade_id < args['max_saccades']:
		env.step()