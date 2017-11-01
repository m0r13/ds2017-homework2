#!/usr/bin/env python2

import sys
import random
from PyQt4 import QtGui, QtCore

class SudokuItemDelegate(QtGui.QItemDelegate):
    def __init__(self, *args, **kwargs):
        super(QtGui.QItemDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        i, j = index.row(), index.column()
        r = option.rect
        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        if i in (3, 6):
            painter.drawLine(QtCore.QLine(r.topLeft(), r.topRight()))
        if j in (3, 6):
            painter.drawLine(QtCore.QLine(r.topLeft(), r.bottomLeft()))
        QtGui.QItemDelegate.paint(self, painter, option, index)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtGui.QMainWindow, self).__init__(*args, **kwargs)

        self.layout = QtGui.QHBoxLayout()
        self.list = QtGui.QListWidget()
        self.table = QtGui.QTableWidget()
        self.table.setRowCount(9)
        self.table.setColumnCount(9)
        for i in range(0, 9):
            for j in range(0, 9):
                item = QtGui.QTableWidgetItem("")
                self.table.setItem(i, j, item)
        self.table.setItemDelegate(SudokuItemDelegate())
        self.table.resizeColumnsToContents()
        self.table.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.table.cellChanged.connect(self.cellChanged)

        self.layout.addWidget(self.list)
        self.layout.addWidget(self.table)
        
        widget = QtGui.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.setScoresState([
            ("Bruno", 73),
            ("Moritz", 42)
        ])
        self.setSudokuState([ [ (random.choice(list(range(1, 10))) if random.random() > 0.7 else 0) for j in range(9) ] for i in range(0, 9) ])
        for row in self.getSudokuState():
            print row

    def cellChanged(self, i, j):
        print "Cell %d:%d changed" % (i, j)
        item = self.table.item(i, j)
        x = str(item.text()).strip()
        if not x:
            return
        if x in map(str, range(1, 10)):
            x = int(x)
            # TODO suggest change to server
            print "Suggest value %d" % x
        else:
            print "Invalid value '%s'!" % x
        self.table.blockSignals(True)
        item.setText("")
        self.table.blockSignals(False)

    def setScoresState(self, scores):
        self.list.clear()
        for player, points in scores:
            self.list.addItem("%s: %s points" % (player, points))

    def setSudokuState(self, sudoku):
        self.table.blockSignals(True)
        for i in range(0, 9):
            for j in range(0, 9):
                x = sudoku[i][j]
                item = self.table.item(i, j)
                flags = item.flags()
                if x == 0:
                    item.setText("")
                    flags |= QtCore.Qt.ItemIsEditable
                else:
                    item.setText(str(x))
                    flags &= ~QtCore.Qt.ItemIsEditable
                flags &= ~QtCore.Qt.ItemIsSelectable
                item.setFlags(flags)
        self.table.blockSignals(False)

    def getSudokuState(self):
        sudoku = []
        for i in range(0, 9):
            row = []
            for j in range(0, 9):
                text = self.table.item(i, j).text()
                if text == "":
                    row.append(0)
                else:
                    row.append(int(text))
            sudoku.append(row)
        return sudoku

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
