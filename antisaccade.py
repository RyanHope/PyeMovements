#!/usr/bin/env python2

import sys,os
import itertools
import types
import simpy
import numpy as np

class AntiSaccadeTask(object):

	def __init__(self, env):
		self.env = env
		self.trial = 0
		self.states = ["FIXATE","GAP","CUE","TARGET","MASK"]
		self.reset()
		self.process = env.process(self.run())

	def reset(self):
		self.trial += 1
		self.fixate_dur = np.random.uniform(1.5,3.5)
		self.mode = np.random.choice(["anti","pro"])
		self.cue_side = np.random.choice(["left","right"])
		self.gap_dur = .2
		self.cue_dur = .4
		self.target_dur = .15
		self.state = 0

	def respond(self, answer):
		self.process.interrupt()
		self.reset()

	def run(self):
		while True:
			try:
				print (self.env.now,self.states[self.state])
				if self.state == 0: # FIXATE
					yield self.env.timeout(self.fixate_dur)
				elif self.state == 1: # GAP
					yield self.env.timeout(self.gap_dur)
				elif self.state == 2: # CUE
					yield self.env.timeout(self.cue_dur)
				elif self.state == 3: # TARGET
					yield self.env.timeout(self.target_dur)
				elif self.state == 4: # MASK
					self.reset()
					#yield self.env.timeout(simpy.core.Infinity)
			except simpy.Interrupt as e:
				pass
			self.state += 1

if __name__ == '__main__':

	env = simpy.Environment()
	ast = AntiSaccadeTask(env)

	while ast.trial <= 10000:
		env.step()
