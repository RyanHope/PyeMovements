#!/usr/bin/env python2
 
import sys, time
from PySide.QtGui import *
from PySide.QtCore import *

from pyqtgraph.parametertree import ParameterTree
from pyqtgraph.widgets.RemoteGraphicsView import RemoteGraphicsView
 
class FixationSignal(QObject):
    sig = Signal()
 
class SimulationWorker(QThread):
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.signal = FixationSignal()
        
    def run(self):
        self.signal.sig.emit()
 
class Simulator(QMainWindow):
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.modelpicker = QComboBox()
        self.paramtree = ParameterTree()
        self.runbutton = QPushButton("Run")
        self.centralwidget = QWidget(self)
        self.fixationplotview = RemoteGraphicsView()
        self.fixationplot = self.fixationplotview.pg.PlotCurveItem()
        self.allplots = self.fixationplotview.pg.GraphicsLayout()
        self.grid = QGridLayout()
        self.grid.addWidget(self.modelpicker)
        self.grid.addWidget(self.paramtree)
        self.grid.addWidget(self.runbutton)
        self.grid.addWidget(self.fixationplotview,0,1,3,1)
        self.fixationplotview.setCentralItem(self.allplots)
        self.p = self.allplots.addPlot()
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setLayout(self.grid)
        self.worker = SimulationWorker()
        self.loadModels()
        
    def loadModels(self):
        self.modelpicker.addItem("CRISP")
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Simulator()
    window.show()
    sys.exit(app.exec_())
