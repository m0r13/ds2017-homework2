#!/usr/bin/env python2

import sys
import random
import time
import threading
import traceback
import socket
import protocol
import Queue
import signal
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

class CreateSessionDialog(QtGui.QDialog):
    def __init__(self, connection, *args, **kwargs):
        super(QtGui.QDialog, self).__init__(*args, **kwargs)

        self.connection = connection
        self.data = None

        self.setModal(True)

        self.name = QtGui.QLineEdit()
        self.numPlayers = QtGui.QSpinBox()
        self.numPlayers.setMinimum(1)
        self.numPlayers.setMaximum(10)
        self.numPlayers.setValue(1)
        self.buttons = QtGui.QDialogButtonBox()
        self.buttons.addButton(QtGui.QDialogButtonBox.Ok)
        self.buttons.addButton(QtGui.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.onAccepted)
        self.buttons.rejected.connect(self.onRejected)

        layout = QtGui.QFormLayout()
        layout.addRow("Session name", self.name)
        layout.addRow("Number of players", self.numPlayers)
        layout.addRow(self.buttons)
        self.setLayout(layout)

    def onAccepted(self):
        name = str(self.name.text()).strip()
        numPlayers = int(self.numPlayers.value())
        if not name:
            QtGui.QMessageBox.critical(self, "Name missing", "You have to insert a session name!")
            return
        self.data = (name, numPlayers)
        self.accept()

    def onRejected(self):
        self.reject()

class LobbyDialog(QtGui.QDialog):
    def __init__(self, connection, *args, **kwargs):
        super(QtGui.QDialog, self).__init__(*args, **kwargs)

        self.connection = connection
        self.connection.sessionJoined.connect(self.onSessionJoined)

        self.setModal(True)

        self.list = QtGui.QListWidget()
        self.list.itemDoubleClicked.connect(self.onConnect)
        self.reloadButton = QtGui.QPushButton("Reload sessions")
        self.reloadButton.clicked.connect(self.onReload)
        self.createButton = QtGui.QPushButton("Create session")
        self.createButton.clicked.connect(self.onCreateSession)
        self.connectButton = QtGui.QPushButton("Connect")
        self.connectButton.clicked.connect(self.onConnect)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.createButton)
        layout.addWidget(self.reloadButton)
        layout.addWidget(self.list)
        layout.addWidget(self.connectButton)
        self.setLayout(layout)

        self.onReload()

    def onReload(self):
        self.connection.sessionsReceived.connect(self.onSessionsReceived)
        self.connection.requestSessions()

    def onSessionsReceived(self, sessions):
        self.connection.sessionsReceived.disconnect()
        self.list.clear()
        for ident, name, cur_players, max_players in sessions:
            item = QtGui.QListWidgetItem("%s: %d/%d players" % (name, cur_players, max_players))
            item.setData(QtCore.Qt.UserRole, ident)
            self.list.addItem(item)

    def onCreateSession(self):
        dialog = CreateSessionDialog(self.connection, self)
        dialog.show()
        dialog.exec_()
        if dialog.result():
            self.connection.createSession(*dialog.data)

    def onConnect(self, _ = None):
        selection = self.list.selectedItems()
        if len(selection) != 1:
            QtGui.QMessageBox.critical(self, "Select a session", "You have to select a session!")
            return
        session = selection[0]
        ident = str(session.data(QtCore.Qt.UserRole).toString())
        self.connection.joinSession(ident)

    def onSessionJoined(self, joined, ident):
        if not joined:
            QtGui.QMessageBox.critical(self, "Session full", "Unable to join session!")
            return
        self.accept()

class MockedNetworkThread(QtCore.QThread):

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal(str)
    usernameAck = QtCore.pyqtSignal(bool)

    sessionsReceived = QtCore.pyqtSignal(object)

    sessionJoined = QtCore.pyqtSignal(bool, str)
    sessionStarted = QtCore.pyqtSignal()
    sudokuReceived = QtCore.pyqtSignal(object)
    scoresReceived = QtCore.pyqtSignal(object)

    suggestNumberAck = QtCore.pyqtSignal(int, int, bool)
    gameOver = QtCore.pyqtSignal(str)

    def __init__(self, host, port, *args, **kwargs):
        super(QtCore.QThread, self).__init__(*args, **kwargs)

        self.host = host
        self.port = port
        self.username = ""

        self.sudoku = None
        self.scores = None

    def run(self):
        time.sleep(0.1)
        self.connected.emit()

    def disconnect(self):
        def disconnected():
            self.disconnected.emit("Disconnected!")
        QtCore.QTimer.singleShot(100, disconnected)

    def setUsername(self, username):
        self.username = username
        def usernameAck():
            ok = random.choice([True, True, True, False])
            ok = True
            self.usernameAck.emit(ok)
        QtCore.QTimer.singleShot(100, usernameAck)

    def requestSessions(self):
        def sessions():
            sessions = [
                (0, "Brunos game", 2, 4),
                (1, "Another game", 4, 4),
            ]
            self.sessionsReceived.emit(sessions)
        QtCore.QTimer.singleShot(1000, sessions)

    def _sessionJoined(self, ident):
        def blah():
            self.sessionJoined.emit(True, ident)
            self.scores = [(self.username, 0)]
            for i in range(3):
                time.sleep(1)
                self.scores.append((["test", "Bruno", "Sander"][i], 0))
                self.scoresReceived.emit(self.scores)
            self.sessionStarted.emit()
            self.sudoku = [ [ (random.choice(list(range(1, 10))) if random.random() > 0.7 else 0) for j in range(9) ] for i in range(0, 9) ]
            self.sudokuReceived.emit(self.sudoku)
        threading.Thread(target=blah).start()

    def joinSession(self, ident):
        print "Joining session %d" % ident
        def response():
            if ident == 1:
                self.sessionJoined.emit(False, -1)
            else:
                self._sessionJoined(ident)
        QtCore.QTimer.singleShot(1000, response)

    def createSession(self, name, numPlayers):
        print "Creating session %s with %d players" % (name, numPlayers)
        def response():
            self._sessionJoined(42)
        QtCore.QTimer.singleShot(1000, response)

    def suggestNumber(self, i, j, number):
        def response():
            if random.choice([True, False]):
                print "Number is ok!"
                self.suggestNumberAck.emit(i, j, True)
                self.scores[0] = (self.scores[0][0], self.scores[0][1] + 1)
                self.sudoku[i][j] = number
            else:
                print "Number is not ok!"
                self.suggestNumberAck.emit(i, j, False)
                self.scores[0] = (self.scores[0][0], self.scores[0][1] - 1)
            self.scoresReceived.emit(self.scores)
            self.sudokuReceived.emit(self.sudoku)
            if random.random() < 0.2:
                self.gameOver.emit(self.username)
        QtCore.QTimer.singleShot(300, response)

    def leaveSession(self):
        pass

class SocketWrapper:
    def __init__(self, socket):
        self.socket = socket
        self.buffer = bytearray("")

    def receive(self):
        try:
            d = self.socket.recv(1024)
            if d:
                self.buffer += d
        except socket.error, e:
            # resource temporarily unavailable if no data in buffer (nonblocking)
            if e.errno != 11:
                raise e

    def available(self):
        return len(self.buffer)

    def recv(self, n):
        while self.available() < n:
            self.receive()
            time.sleep(0.01)
        data = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return data

    def sendall(self, data):
        self.socket.sendall(data)

class NetworkThread(QtCore.QThread):

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal(str)
    usernameAck = QtCore.pyqtSignal(bool)

    sessionsReceived = QtCore.pyqtSignal(object)

    sessionJoined = QtCore.pyqtSignal(bool, str)
    sessionStarted = QtCore.pyqtSignal()
    sudokuReceived = QtCore.pyqtSignal(object)
    scoresReceived = QtCore.pyqtSignal(object)

    suggestNumberAck = QtCore.pyqtSignal(int, int, bool)
    gameOver = QtCore.pyqtSignal(str)

    def __init__(self, host, port, *args, **kwargs):
        super(QtCore.QThread, self).__init__(*args, **kwargs)

        self.host = host
        self.port = port
        self.socket = None
        self.package_queue = Queue.Queue()
        self.stop = False
        self.username = ""

    def run(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setblocking(False)
            stream = SocketWrapper(self.socket)
            self.connected.emit()
            while not self.stop:
                stream.receive()
                while stream.available():
                    pkg_type, data = protocol.read_package(stream)
                    print "Received: %d, %s" % (pkg_type, data)

                    if pkg_type == protocol.PKG_HELLO_ACK:
                        self.usernameAck.emit(data["ok"])
                    if pkg_type == protocol.PKG_SESSIONS:
                        self.sessionsReceived.emit(data["sessions"])
                    if pkg_type == protocol.PKG_SESSION_JOINED:
                        self.sessionJoined.emit(data["ok"], data["uuid"])

                while not self.package_queue.empty():
                    pkg_type, data = self.package_queue.get()
                    print "Writing: %d, %s" % (pkg_type, data)
                    protocol.write_package(stream, pkg_type, data)

                time.sleep(0.01)

            self.socket.close()
            self.disconnected.emit("Disconnected!")
        except socket.error, e:
            traceback.print_exc()
            self.disconnected.emit(str(e))

    def disconnect(self):
        self.stop = True

    def setUsername(self, username):
        self.package_queue.put((protocol.PKG_HELLO, {"username" : username}))

    def requestSessions(self):
        self.package_queue.put((protocol.PKG_GET_SESSIONS, {}))

    def joinSession(self, ident):
        self.package_queue.put((protocol.PKG_JOIN_SESSION, {"uuid" : ident}))

    def createSession(self, name, numPlayers):
        self.package_queue.put((protocol.PKG_CREATE_SESSION, {"name" : name, "num_players" : numPlayers}))

    def suggestNumber(self, i, j, number):
        pass

    def leaveSession(self):
        pass

class MainWindow(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtGui.QMainWindow, self).__init__(*args, **kwargs)

        self.list = QtGui.QListWidget()
        self.leaveSessionButton = QtGui.QPushButton("Leave session")
        self.leaveSessionButton.setEnabled(False)
        self.leaveSessionButton.clicked.connect(self.doLeaveSession)
        self.disconnectButton = QtGui.QPushButton("Disconnect from server")
        self.disconnectButton.setEnabled(False)
        self.disconnectButton.clicked.connect(self.doDisconnect)
        self.table = QtGui.QTableWidget()
        self.table.setRowCount(9)
        self.table.setColumnCount(9)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        for i in range(0, 9):
            for j in range(0, 9):
                item = QtGui.QTableWidgetItem("")
                self.table.setItem(i, j, item)
        self.table.setItemDelegate(SudokuItemDelegate())
        self.table.resizeColumnsToContents()
        self.table.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.table.cellChanged.connect(self.cellChanged)
 
        layout = QtGui.QHBoxLayout()
        leftLayout = QtGui.QVBoxLayout()
        leftLayout.addWidget(self.list)
        leftLayout.addWidget(self.leaveSessionButton)
        leftLayout.addWidget(self.disconnectButton)
        layout.addLayout(leftLayout)
        layout.addWidget(self.table)
        widget = QtGui.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.status = QtGui.QStatusBar()
        self.setStatusBar(self.status)

        self.thread = None

        self.setScoresState([])
        self.setSudokuState([[0]*9] * 9)
        self.table.setEnabled(False)

        QtCore.QTimer.singleShot(10, self.doConnect)

    def doConnect(self):
        address, ok = QtGui.QInputDialog.getText(self, "Server address", "Please enter the server address and port (host:port):", QtGui.QLineEdit.Normal, "localhost:8888")
        if not ok:
            self.close()
            return
        address = str(address)
        host, port = address, protocol.SERVER_PORT
        if ":" in address:
            host, port = address.split(":")
            port = int(port)

        self.status.showMessage("Connecting...")
        # TODO check if there is already a connection / thread ?
        assert self.thread is None
        self.thread = NetworkThread(host, port)
        self.thread.connected.connect(self.onConnected)
        self.thread.disconnected.connect(self.onDisconnected)
        self.thread.usernameAck.connect(self.onUsernameAck)
        self.thread.sessionJoined.connect(self.onSessionJoined)
        self.thread.sessionStarted.connect(self.onSessionStarted)
        self.thread.sudokuReceived.connect(self.onSudokuReceived)
        self.thread.scoresReceived.connect(self.onScoresReceived)
        self.thread.gameOver.connect(self.onGameOver)
        self.thread.start()

    def doRequestUsername(self):
        name, ok = "", False
        while not ok:
            name, ok = QtGui.QInputDialog.getText(self, "Username", "Please enter your username:", QtGui.QLineEdit.Normal, "ricky.a87")
            name = str(name).strip()
            ok = ok and bool(name)
            if not ok:
                QtGui.QMessageBox.critical(self, "Username required", "You have to enter a username!")
        self.thread.setUsername(name)

    def onConnected(self):
        self.disconnectButton.setEnabled(True)
        self.status.showMessage("Connected")
        self.doRequestUsername()

    def onUsernameAck(self, ok):
        if ok:
            self.status.showMessage("Connected as %s" % self.thread.username)
            self.doLobby()
        else:
            QtGui.QMessageBox.critical(self, "Username taken", "The username is already taken! Please try another one.")
            self.doRequestUsername()

    def doLobby(self):
        self.setScoresState([])
        self.setSudokuState([[0]*9] * 9)
        self.table.setEnabled(False)

        result = False
        while not result:
            dialog = LobbyDialog(self.thread, self)
            dialog.show()
            dialog.exec_()
            result = dialog.result()
            if not result:
                r = QtGui.QMessageBox.question(self, "Disconnect from server", "Do you want to disconnect from the server?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                if r == QtGui.QMessageBox.Yes:
                    self.doDisconnect()
                    return

    def onSessionJoined(self, ok, ident):
        # TODO connect this!
        self.leaveSessionButton.setEnabled(True)

    def onSessionStarted(self):
        self.table.setEnabled(True)

    def onSudokuReceived(self, sudoku):
        self.setSudokuState(sudoku)

    def onScoresReceived(self, scores):
        self.setScoresState(scores)

    def doLeaveSession(self):
        self.leaveSessionButton.setEnabled(False)
        self.doLobby()

    def onGameOver(self, winner):
        self.leaveSessionButton.setEnabled(False)
        QtGui.QMessageBox.information(self, "Game is over", "The game is over. Winner is: %s" % winner)
        self.doLobby()

    def doDisconnect(self):
        self.leaveSessionButton.setEnabled(False)
        self.setScoresState([])
        self.setSudokuState([[0]*9] * 9)
        self.table.setEnabled(False)
        self.thread.disconnect()

    def onDisconnected(self, reason):
        self.disconnectButton.setEnabled(False)

        self.thread.wait()
        self.thread = None
        QtGui.QMessageBox.information(self, "Disconnected", "Disconnected from server:\n" + reason)
        self.doConnect()

    def cellChanged(self, i, j):
        print "Cell %d:%d changed" % (i, j)
        item = self.table.item(i, j)
        x = str(item.text()).strip()
        if not x:
            return
        if x in map(str, range(1, 10)):
            x = int(x)
            print "Suggest value %d" % x
            self.thread.suggestNumber(i, j, x)
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


def sigint_handler(*args):
    sys.stderr.write('Got SIGINT, quitting...')
    QtGui.QApplication.quit()
        
if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
