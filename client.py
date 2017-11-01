#!/usr/bin/env python2

import sys
from PyQt4 import QtGui, QtCore

class MainWindow(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtGui.QMainWindow, self).__init__(*args, **kwargs)

        self.table = QtGui.QTableWidget()
        self.table.setRowCount(9)
        self.table.setColumnCount(9)
        self.setCentralWidget(self.table)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
