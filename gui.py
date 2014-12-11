#!/usr/bin/env python2

# http://www.pyqtgraph.org/documentation/
# http://www.matteomattei.com/pyside-signals-and-slots-with-qthread-example/
# http://zetcode.com/gui/pysidetutorial/
# http://qt-project.org/wiki/PySideDocumentation
# http://qt-project.org/doc/qt-4.8/gallery-plastique.html

import sys, time
from PySide.QtGui import *
from PySide.QtCore import *

from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.widgets.RemoteGraphicsView import RemoteGraphicsView

from CRISP import *
import simpy
 
class EventSignal(QObject):
    sig = Signal(str)
 
class CRISPWorker(QThread):
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.events = EventSignal()
        
    def init_simulation(self, max_saccades, timer_states, timer_mean, labile_mean, nonlabile_mean, exec_mean):
        self.max_saccades = max_saccades
        self.env = simpy.Environment()
        def env_log(self, id, stage, status):
            sac_id = self.saccade_id if self.active_saccades>0 else 0
            fix_id = self.fixation_id if self.active_saccades==0 else 0
            if stage=="execution":
                fix_id = self.fixation_id
            print "%f\t%d\t%d\t%d\tsaccade-%d\t%s\t%s" % (self.now, self.active_saccades, sac_id, fix_id, id, stage, status)
        self.env.log = types.MethodType(env_log, self.env)   
        self.env.active_saccades = 0
        self.env.saccade_id = 0
        self.env.fixation_id = 1
        self.env.fixation_start = 0
        self.env.fixation_durations = []
        self.saccade_exec = SaccadeExec(self.env, mean=exec_mean)
        self.saccade_programmer = SaccadeProgrammer(self.env, self.saccade_exec, mean=nonlabile_mean)
        self.saccade_planner = SaccadePlanner(self.env, self.saccade_programmer, mean=labile_mean)
        self.brainstem_oscillator = BrainstemOscillator(self.env, self.saccade_planner, mean=timer_mean, states=timer_states)

    def run(self):
        while (not self.exiting and (self.env.saccade_id < self.max_saccades or (self.env.saccade_id == self.max_saccades and self.env.active_saccades > 0))):
            self.env.step()
        self.events.sig.emit("done")
 
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
        
        self.centralwidget = QWidget(self)
        self.fixationplotview = RemoteGraphicsView()
        self.fixationplot = self.fixationplotview.pg.PlotCurveItem()
        self.allplots = self.fixationplotview.pg.GraphicsLayout()
        self.grid = QGridLayout()
        self.grid.addWidget(self.modelpicker,0,0,1,2)
        self.grid.addWidget(self.paramtree,1,0,1,2)
        self.grid.addWidget(self.nsaccadelab,2,0,1,1)
        self.grid.addWidget(self.nsaccades,2,1,1,1)
        self.grid.addWidget(self.runbutton,3,0,1,2)
        self.grid.addWidget(self.fixationplotview,0,2,4,1)
        self.fixationplotview.setCentralItem(self.allplots)
        self.p = self.allplots.addPlot()
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setLayout(self.grid)
        
        self.runsignal = EventSignal()
        self.worker = CRISPWorker()
        self.worker.events.sig.connect(self.handle_worker_events)
        
    def handle_runbutton_clicked(self):
        if self.worker.isRunning():
            self.worker.exiting = True
            self.runbutton.setEnabled(False)
            while self.worker.isRunning():
                time.sleep(0.01)
                continue
            self.runbutton.setText('Start simulation')
            self.runbutton.setEnabled(True)
        else:
            self.worker.exiting = False
            print self.nsaccades.value()
            self.worker.init_simulation(self.nsaccades.value(),
                                        self.modelparams.param("Brainstem Oscillator", "Random Walk States").value(),
                                        self.modelparams.param("Brainstem Oscillator", "Average Duration (ms)").value(),
                                        self.modelparams.param("Saccade Planner", "Average Duration (ms)").value(),
                                        self.modelparams.param("Saccade Programmer", "Average Duration (ms)").value(),
                                        self.modelparams.param("Saccade Exec", "Average Duration (ms)").value())
            self.worker.start()
            self.runbutton.setEnabled(False)
            while not self.worker.isRunning():
                time.sleep(0.01)
                continue
            self.runbutton.setText('Stop simulation')
            
    def handle_worker_events(self, event):
        if event == "done":
            self.runbutton.setText('Start simulation')
            self.runbutton.setEnabled(True)
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Simulator()
    window.show()
    sys.exit(app.exec_())
