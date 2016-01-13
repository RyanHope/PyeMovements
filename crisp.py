#!/usr/bin/env python2

import sys,os
import itertools
import types
import simpy
import numpy as np

class Timer(object):
	__alias__ = "timer"
	def __init__(self, env, labile, mean=.250, states=11, start_state=0, rate=1.0):
		self.env = env
		self.labile = labile
		self.setStates(states)
		self.setMean(mean)
		self.setRate(rate)
		if start_state == -1:
			self.start_state = np.random.randint(self.states)
		elif start_state >= self.states:
			self.start_state = self.states - 1
		else:
			self.start_state = start_state
		self.process = env.process(self.run())

	def setStates(self, states):
		self.states = states
		self.env.log(0, self.__alias__, "set_states", self.states)

	def setMean(self, mean):
		self.mean = mean
		self.env.log(0, self.__alias__, "set_mean", self.mean)

	def setRate(self, rate):
		self.rate = rate
		self.env.log(0, self.__alias__, "set_rate", self.rate)

	def next_state(self):
		yield self.env.timeout(-(1/((self.states/self.mean)*self.rate))*np.log(1-np.random.uniform()))

	def run(self):
		for i in itertools.count(1):
			for j in itertools.count(self.start_state):
				if j < self.states:
					yield self.env.process(self.next_state())
					self.env.log(i, self.__alias__, "next_state", j, self.states)
				else:
					break
			self.env.log(i, self.__alias__, "reset")
			self.setRate(1.0)
			self.labile.process.interrupt(i)
			self.start_state = 0

class LabileProg(object):
	__alias__ = "labile_programming"
	def __init__(self, env, nonlabile, attn=None, mean=.180, stdev=3, alpha=1):
		self.env = env
		self.nonlabile = nonlabile
		self.attn = attn
		self.setAlpha(alpha)
		self.setMean(mean)
		self.setStdev(stdev)
		self.next_event = 0
		self.process = env.process(self.run())
		self.restarts = 0
		self.target = 0
		
	def getTarget(self):
		pass

	def setAlpha(self, alpha):
		self.alpha = alpha
		self.env.log(0, self.__alias__, "set_alpha", self.alpha)

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
					self.getTarget()
					yield self.env.timeout(self.next_event)
					self.next_event = 0
				except simpy.Interrupt as e:
					if e.cause == -1:
						self.env.log(self.spid, self.__alias__, "canceled")
						self.next_event = simpy.core.Infinity
					else:
						if self.next_event < simpy.core.Infinity:
							self.env.log(self.spid, self.__alias__, "restarted")
							self.restarts += 1
						self.spid = e.cause
						self.next_event = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
														  (self.stdev*self.stdev)/self.mean)
						self.env.log(self.spid, self.__alias__, "started")
			#self.getTarget()
			self.env.log(self.spid, self.__alias__, "complete", self.restarts, self.target)
			self.restarts = 0
			self.nonlabile.process.interrupt((self.spid,self.target))

class NonLabileProg(object):
	__alias__ = "nonlabile_programming"
	def __init__(self, env, sp, mean=.040, stdev=3):
		self.env = env
		self.sp = sp
		self.setMean(mean)
		self.setStdev(stdev)
		self.next_event = 0
		self.process = env.process(self.run())
		self.restarts = 0

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
					yield self.env.timeout(self.next_event)
					self.next_event = 0
				except simpy.Interrupt as e:
					if self.next_event < simpy.core.Infinity:
						self.env.log(self.spid, self.__alias__, "restarted")
						self.restarts += 1
					self.spid, self.target = e.cause
					self.next_event = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
													  (self.stdev*self.stdev)/self.mean)
					self.env.log(self.spid, self.__alias__, "started", self.target)
			self.env.log(self.spid, self.__alias__, "complete", self.target)
			self.restarts = 0
			self.sp.process.interrupt((self.spid, self.target))

class SaccadeExec(object):
	__alias__ = "saccade_execution"
	def __init__(self, env, pv, mean=.040, stdev=3):
		self.env = env
		self.pv = pv
		self.setMean(mean)
		self.setStdev(stdev)
		self.next_event = 0
		self.process = env.process(self.run())
		self.saccades = 0
		self.mergers = 0
		self.setPosition()

	def setPosition(self):
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
					yield self.env.timeout(self.next_event)
					self.next_event = 0
				except simpy.Interrupt as e:
					self.spid, self.position = e.cause
					if self.next_event < simpy.core.Infinity:
						self.env.log(self.spid, self.__alias__, "merged")
						self.mergers += 1
					self.next_event = np.random.gamma((self.mean*self.mean)/(self.stdev*self.stdev),
													  (self.stdev*self.stdev)/self.mean)
					self.saccades += 1
					self.pv.process.interrupt((self.spid, True))
					self.env.log(self.spid, self.__alias__, "started", self.mergers, self.saccades, self.position)
			self.setPosition()
			self.env.log(self.spid, self.__alias__, "complete", self.mergers, self.saccades, self.position)
			self.mergers = 0
			self.pv.process.interrupt((self.spid, False))

class ProcessVision(object):

	def __init__(self, env):
		self.env = env
		self.process = env.process(self.run())
		self.fixations = 1

	def run(self):
		self.env.log(1, "fixation", "started")
		while True:
			try:
				yield self.env.timeout(simpy.core.Infinity)
			except simpy.Interrupt as e:
				if e.cause[1]:
					self.env.log(-1, "fixation", "complete", self.fixations)
				else:
					self.fixations += 1
					self.env.log(-1, "fixation", "started", self.fixations)

class CRISPEnvironment(simpy.Environment):

	def __init__(self, args, initial_time=0.0):
		super(CRISPEnvironment, self).__init__(initial_time)
		self.debug = False
		self.stop = -1

	def log(self, *args):
		if self.stop==-1:
			e = [-1] + list(args)
		else:
			e = [self.now] + list(args)
			if self.efun(e):
				self.stop = True
		if self.debug:
			sys.stderr.write(str(e))
			sys.stderr.write("\n")
			sys.stderr.flush()
		return e

	def run_while(self, efun):
		self.efun = efun
		self.stop = 0
		while self.stop==0:
			self.step()


if __name__ == '__main__':

	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--max-saccades", type=int, default=1)
	parser.add_argument("--timer_mean", type=float, action="store", default=.250)
	parser.add_argument("--timer_states", type=int, default=11)
	parser.add_argument("--timer_start_state", type=int, default=-1)
	parser.add_argument("--labile_mean", type=float, action="store", default=.180)
	parser.add_argument("--labile_stdev", type=float, action="store", default=.060)
	parser.add_argument("--nonlabile_mean", type=float, action="store", default=.040)
	parser.add_argument("--nonlabile_stdev", type=float, action="store", default=.010)
	parser.add_argument("--exec_mean", type=float, action="store", default=.040)
	parser.add_argument("--exec_stdev", type=float, action="store", default=.010)
	args = vars(parser.parse_args())

	env = CRISPEnvironment(args)

	# Create components
	processVision = ProcessVision(env)
	saccadeExec = SaccadeExec(env, processVision, mean=args['exec_mean'])
	nonLabileProg = NonLabileProg(env, saccadeExec, mean=args['nonlabile_mean'])
	labileProg = LabileProg(env, nonLabileProg, mean=args['labile_mean'])
	timer = Timer(env, labileProg, mean=args['timer_mean'], states=args['timer_states'], start_state=args['timer_start_state'])

	# Run
	env.run_while(lambda e: e[2]=="saccade_execution" and e[3]=="complete" and e[5]==args["max_saccades"])
