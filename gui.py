#!/usr/bin/env python2

# http://www.pyqtgraph.org/documentation/
# http://www.matteomattei.com/pyside-signals-and-slots-with-qthread-example/
# http://zetcode.com/gui/pysidetutorial/
# http://qt-project.org/wiki/PySideDocumentation
# http://qt-project.org/doc/qt-4.8/gallery-plastique.html

import sys, time
from PySide.QtGui import *
from PySide.QtCore import *

import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
#from pyqtgraph.widgets.RemoteGraphicsView import RemoteGraphicsView

from CRISP import *
import simpy

import numpy as np

class EventSignal(QObject):
    sig = Signal(str,object)

class GUIEnvironment(LoggingEnvironment):
    def __init__(self, args, qtevents, output=sys.__stdout__, initial_time=0):
        super(GUIEnvironment, self).__init__(args, output=output, initial_time=initial_time)
        self.qtevents = qtevents
    def log(self, id, stage, status):
        super(GUIEnvironment, self).log(id, stage, status)
        if stage=="execution" and status=="started":
            self.qtevents.sig.emit("fixations",self.fixation_durations)

class CRISPWorker(QThread):

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.paused = False
        self.events = EventSignal()

    def init_simulation(self, args):
        self.max_saccades = args['max_saccades']
        self.env = GUIEnvironment(args, self.events)
        self.saccade_exec = SaccadeExec(self.env, mean=args['exec_mean'])
        self.saccade_programmer = SaccadeProgrammer(self.env, self.saccade_exec, mean=args['nonlabile_mean'])
        self.saccade_planner = SaccadePlanner(self.env, self.saccade_programmer, mean=args['labile_mean'])
        self.brainstem_oscillator = BrainstemOscillator(self.env, self.saccade_planner, mean=args['timer_mean'], states=args['timer_states'])

    def run(self):
        while (not self.exiting) and self.env.saccade_id < self.max_saccades:
            if not self.paused:
                self.env.step()
            self.yieldCurrentThread()
        self.events.sig.emit("done",self.exiting)

class Simulator(QMainWindow):

    params = [{'name': 'Brainstem Oscillator', 'type': 'group', 'children':
               [{'name': 'Random Walk States', 'type': 'int', 'value': 11},
                {'name': 'Average Duration (ms)', 'type': 'float', 'value': .250}]},
              {'name': 'Saccade Planner', 'type': 'group', 'children':
               [{'name': 'Average Duration (ms)', 'type': 'float', 'value': .180}]},
              {'name': 'Saccade Programmer', 'type': 'group', 'children':
               [{'name': 'Average Duration (ms)', 'type': 'float', 'value': .040}]},
              {'name': 'Saccade Exec', 'type': 'group', 'children':
               [{'name': 'Average Duration (ms)', 'type': 'float', 'value': .040}]}]

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle("PyeMovements")

        self.modelpicker = QComboBox()
        self.modelpicker.addItem("CRISP")

        self.modelparams = Parameter.create(name='params', type='group', children=self.params)
        self.paramtree = ParameterTree()
        self.paramtree.setParameters(self.modelparams, showTop=False)

        self.nsaccadelab = QLabel("# Saccades")
        self.nsaccadelab.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.nsaccades = QSpinBox()
        self.nsaccades.setRange(1,1000000)
        self.nsaccades.setValue(10000)

        self.runbutton = QPushButton("Start simulation")
        self.runbutton.clicked.connect(self.handle_runbutton_clicked)
        self.resetbutton = QPushButton("Reset simulation")
        self.resetbutton.setEnabled(False)
        self.resetbutton.clicked.connect(self.handle_resetbutton_clicked)

        self.centralwidget = QWidget(self)

        self.fixation_plot_widget = pg.PlotWidget(title="Fixation Duration Histogram",labels={"left":"Count","bottom":"Duration (s)"})
        self.fixation_plot_data = pg.PlotDataItem()

        self.grid = QGridLayout()
        self.grid.addWidget(self.modelpicker,0,0,1,2)
        self.grid.addWidget(self.paramtree,1,0,1,2)
        self.grid.addWidget(self.nsaccadelab,2,0,1,1)
        self.grid.addWidget(self.nsaccades,2,1,1,1)
        self.grid.addWidget(self.runbutton,3,0,1,1)
        self.grid.addWidget(self.resetbutton,3,1,1,1)
        self.grid.addWidget(self.fixation_plot_widget,0,2,4,1)

        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setLayout(self.grid)

        self.sim_reset()

        self.plots_timer = QTimer()
        self.plots_timer.timeout.connect(self.updateFixationPlot)
        self.plots_timer.start(50)

    def updateFixationPlot(self):
        if self.data_fixations != []:
            y,x = np.histogram(self.data_fixations, bins=np.linspace(0, 1, 100))
            self.fixation_plot_data.setData(x, y, stepMode=True, fillLevel=0, brush=(0,0,255,150))

    def sim_reset(self):
        self.fixation_plot_widget.clear()
        if hasattr(self, 'worker') and self.worker != None:
            self.worker.exiting = True
            while self.worker.isRunning():
                time.sleep(0)
            self.worker.quit()
            self.worker.wait()
        self.worker = None
        self.data_fixations = []

    def sim_start(self):
        self.worker = CRISPWorker()
        self.worker.init_simulation({
            "max_saccades":self.nsaccades.value(),
            "timer_states":self.modelparams.param("Brainstem Oscillator", "Random Walk States").value(),
            "timer_mean":self.modelparams.param("Brainstem Oscillator", "Average Duration (ms)").value(),
            "labile_mean":self.modelparams.param("Saccade Planner", "Average Duration (ms)").value(),
            "nonlabile_mean":self.modelparams.param("Saccade Programmer", "Average Duration (ms)").value(),
            "exec_mean":self.modelparams.param("Saccade Exec", "Average Duration (ms)").value()
        })
        self.worker.events.sig.connect(self.handle_worker_events)
        self.worker.start()
        while not self.worker.isRunning():
            time.sleep(0)
        self.fixation_plot_widget.addItem(self.fixation_plot_data)

    def handle_resetbutton_clicked(self):
        self.runbutton.setText('Start simulation')
        self.runbutton.setEnabled(False)
        self.resetbutton.setEnabled(False)
        self.sim_reset()
        self.runbutton.setEnabled(True)

    def handle_runbutton_clicked(self):
        if not self.worker:
            self.runbutton.setEnabled(False)
            self.sim_start()
            self.runbutton.setText('Pause simulation')
            self.runbutton.setEnabled(True)
            self.resetbutton.setEnabled(True)
        elif self.worker.isRunning():
            if self.worker.paused:
                self.worker.paused = False
                self.runbutton.setText('Pause simulation')
            else:
                self.worker.paused = True
                self.runbutton.setText('Resume simulation')

    def handle_worker_events(self, event, data):
        if event == "fixations":
            self.data_fixations = data

    def exitHandler(self):
        self.sim_reset()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Simulator()
    app.aboutToQuit.connect(window.exitHandler)
    window.show()
    window.raise_()
    sys.exit(app.exec_())
