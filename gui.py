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
 
class FixationSignal(QObject):
    sig = Signal()
 
class CRISPWorker(QThread):
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.signal = FixationSignal()
        
    def run(self):
        self.signal.sig.emit()
 
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
        
        self.runbutton = QPushButton("Run")
        
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
        self.worker = CRISPWorker()
        
        print self.modelparams.param("Saccade Planner", "Average Duration (ms)").value()
        
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Simulator()
    window.show()
    sys.exit(app.exec_())
