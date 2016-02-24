#!/usr/bin/env python

import sys,os
import itertools
import types
import simpy
import numpy as np

from crisp import *

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
                    mm = self.mean*self.mean
                    ss = self.stdev*self.stdev
                    self.next_event = np.random.gamma(mm/ss,ss/self.mean)
                    self.env.log(-1, self.__alias__, "started", self.target)
            self.env.log(-1, self.__alias__, "complete", self.target)
            self.position = self.event.value
            self.restarts = 0
