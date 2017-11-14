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
import util
from PyQt4 import QtGui, QtCore

class SudokuItemDelegate(QtGui.QItemDelegate):
    """Helper class to style cells of 9x9 sudoku into 3x3 fields again."""
    def __init__(self, *args, **kwargs):
        super(QtGui.QItemDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        """Custom paint method that handles drawing lines for 3x3 fields."""
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
    """Custom dialog that is used to receive user input for creating a session."""
    def __init__(self, connection, *args, **kwargs):
        super(QtGui.QDialog, self).__init__(*args, **kwargs)

        # data entered by user: when entered tuple (game name, number of players)
        self.data = None

        # ui setup
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
        """Called when the OK-button is pressed."""
        # take ui input
        name = str(self.name.text()).strip()
        numPlayers = int(self.numPlayers.value())
        # validate ui input
        if not name:
            QtGui.QMessageBox.critical(self, "Name missing", "You have to insert a session name!")
            return
        # save it, close dialog successfully
        self.data = (name, numPlayers)
        self.accept()

    def onRejected(self):
        """Called when the cancel-button is pressed."""
        # do nothing. just close dialog
        self.reject()

class LobbyDialog(QtGui.QDialog):
    """Custom dialog that is used to present running sessions to user and choice to join/create one."""
    def __init__(self, connection, *args, **kwargs):
        super(QtGui.QDialog, self).__init__(*args, **kwargs)

        # connection to server
        self.connection = connection
        self.connection.sessionJoined.connect(self.onSessionJoined)

        # ui setup
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

        # load list of sessions in the beginning
        self.onReload()

    def onReload(self):
        """Is called once reload button is clicked and at dialog setup."""
        # request sessions, will be received in self.onSessionsReceived
        self.connection.sessionsReceived.connect(self.onSessionsReceived)
        self.connection.requestSessions()

    def onSessionsReceived(self, sessions):
        """Is called when list of sessions has arrived from server."""
        self.connection.sessionsReceived.disconnect()
        # clear list of sessions, load new list
        self.list.clear()
        for ident, name, cur_players, max_players in sessions:
            item = QtGui.QListWidgetItem("%s: %d/%d players" % (name, cur_players, max_players))
            item.setData(QtCore.Qt.UserRole, ident)
            self.list.addItem(item)

    def onCreateSession(self):
        """Is called when the 'create session'-button is clicked."""
        # create dialog that collects user input to create session
        dialog = CreateSessionDialog(self.connection, self)
        dialog.show()
        dialog.exec_()
        if dialog.result():
            # when dialog input successful: create session on server
            # dialog.data is tuple (session name, number of players) which are also arguments of createSession function
            self.connection.createSession(*dialog.data)

    def onConnect(self, _ = None):
        """Is called when the connection button is pressed or an item
        in the session list is double-clicked (unused argument _ is for that)."""
        # get selection, make sure exactly one item is selected
        selection = self.list.selectedItems()
        if len(selection) != 1:
            QtGui.QMessageBox.critical(self, "Select a session", "You have to select a session!")
            return
        session = selection[0]
        # get id of session, connect to it
        ident = str(session.data(QtCore.Qt.UserRole).toString())
        self.connection.joinSession(ident)

    def onSessionJoined(self, joined, ident):
        """Is called when response from server after joining-session request arrived."""
        # close the dialog if joining session was successful
        # show error if session is already full
        if not joined:
            QtGui.QMessageBox.critical(self, "Session full", "Unable to join session!")
            return
        self.accept()

class NetworkThread(QtCore.QThread):
    """Class that runs as thread and manages the connection to the sudoku server"""

    # Qt signals that can one can subscribe to
    # and that show the arrival of different packages from the server
    # arguments are the fields of associated protocol packages

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
        """Mainloop of server connection."""
        try:
            # try to connect to server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setblocking(False)
            stream = util.SocketWrapper(self.socket)
            self.connected.emit()

            # handle packages in loop until disconnect
            while not self.stop:
                # attempt to read data from the socket
                stream.receive()
                # while there is data available, read packages
                while stream.available():
                    # read package
                    pkg_type, data = protocol.read_package(stream)
                    print "Received: %d, %s" % (pkg_type, data)

                    # depending on the package type, fire associated signal
                    if pkg_type == protocol.PKG_HELLO_ACK:
                        self.usernameAck.emit(data["ok"])
                    if pkg_type == protocol.PKG_SESSIONS:
                        self.sessionsReceived.emit(data["sessions"])
                    if pkg_type == protocol.PKG_SESSION_JOINED:
                        self.sessionJoined.emit(data["ok"], data["uuid"])
                    if pkg_type == protocol.PKG_SESSION_STARTED:
                        self.sessionStarted.emit()
                    if pkg_type == protocol.PKG_SUDOKU_STATE:
                        # sudoku state arrives as flattened array with 89 ints
                        # --> convert it to 9x9 array
                        sudoku = []
                        for i in range(9):
                            sudoku.append(data["sudoku"][(i*9):(i*9+9)])
                        self.sudokuReceived.emit(sudoku)
                    if pkg_type == protocol.PKG_SCORES_STATE:
                        self.scoresReceived.emit(data["scores"])
                    if pkg_type == protocol.PKG_SUGGEST_NUMBER_ACK:
                        self.suggestNumberAck.emit(data["i"], data["j"], data["ok"])
                    if pkg_type == protocol.PKG_GAME_OVER:
                        self.gameOver.emit(data["winner"])

                # then send packages to server that are in queue
                while not self.package_queue.empty():
                    pkg_type, data = self.package_queue.get()
                    print "Writing: %d, %s" % (pkg_type, data)
                    protocol.write_package(stream, pkg_type, data)

                # then wait a bit
                time.sleep(0.01)

            # disconnect
            self.socket.close()
            self.disconnected.emit("Disconnected!")
        except socket.error, e:
            # handle possible socket errors
            traceback.print_exc()
            self.disconnected.emit(str(e))

    """Following functions are actions that the client can perform on the server.
    To send package data over the socket to the server in the server-connection thread,
    packages beloging to specific actions are put into a queue by the ui thread which
    are then sent by the server-connection thread."""

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
        self.package_queue.put((protocol.PKG_SUGGEST_NUMBER, {"i" : i, "j" : j, "number" : number}))

    def leaveSession(self):
        self.package_queue.put((protocol.PKG_LEAVE_SESSION, {}))

class MainWindow(QtGui.QMainWindow):
    """Main sudoku game window."""

    """Time in milliseconds that number suggestions by the player
    are highlighted depending on server response (right number / wrong number)."""
    NUMBER_ACK_HIGHLIGHT_TIME = 1000

    def __init__(self, *args, **kwargs):
        super(QtGui.QMainWindow, self).__init__(*args, **kwargs)

        # ui setup
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
        # call function self.doSuggestNumber when a cell of the sudoku table is edited by the user
        self.table.cellChanged.connect(self.doSuggestNumber)
 
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

        self.disableGame()

        # connection to server
        # will be instance of ServerThread
        self.connection = None
        self.openedDialog = None

        # start sudoku game state machine with server connection dialog
        # for ui fancyfying: show it after window is actually visible
        QtCore.QTimer.singleShot(10, self.doConnect)

    def doConnect(self):
        """Called at the start of application or when server connection is lost / disconnected."""
        # request server address
        address, ok = QtGui.QInputDialog.getText(self, "Server address", "Please enter the server address and port (host:port):", QtGui.QLineEdit.Normal, "localhost:8888")
        # close application if cancel was pressed
        if not ok:
            self.close()
            return
        # validate address / port
        address = str(address)
        host, port = address, protocol.SERVER_PORT
        if ":" in address:
            host, port = address.split(":")
            port = int(port)

        # there may be no server connection thread active at this point
        assert self.connection is None
        # create thread that handles connection to server
        # connect signals of thread to ui methods handling them
        self.connection = NetworkThread(host, port)
        self.connection.connected.connect(self.onConnected)
        self.connection.disconnected.connect(self.onDisconnected)
        self.connection.usernameAck.connect(self.onUsernameAck)
        self.connection.sessionJoined.connect(self.onSessionJoined)
        self.connection.sessionStarted.connect(self.onSessionStarted)
        self.connection.sudokuReceived.connect(self.onSudokuReceived)
        self.connection.scoresReceived.connect(self.onScoresReceived)
        self.connection.suggestNumberAck.connect(self.onSuggestNumberAck)
        self.connection.gameOver.connect(self.onGameOver)
        self.connection.start()

    def onConnected(self):
        """Is called when the client is connected to the server."""
        # ui status handling
        self.disconnectButton.setEnabled(True)
        # next step: request username
        self.doRequestUsername()

    def doRequestUsername(self):
        """Is called when the client is connected to the server and a username shall be sent to the server"""
        # request username in ui from user
        name, ok = "", False
        while not ok:
            name, ok = QtGui.QInputDialog.getText(self, "Username", "Please enter your username:", QtGui.QLineEdit.Normal, "ricky.a87")
            # connection lost in-between, just return from here
            if not ok and not self.connection:
                return
            name = str(name).strip()
            ok = ok and bool(name)
            if not ok:
                QtGui.QMessageBox.critical(self, "Username required", "You have to enter a username!")
                # connection lost
                if not self.connection:
                    return
        # send to server
        self.connection.setUsername(name)

    def onUsernameAck(self, ok):
        """Is called when the username was sent to the server and the server acknowledged that."""
        # username is not taken yet -> ok -> go to "lobby" (list / join / create session)
        if ok:
            self.doLobby()
        # username is taken yet. show error and let user try it again
        else:
            QtGui.QMessageBox.critical(self, "Username taken", "The username is already taken! Please try another one.")
            # connection lost
            if not self.connection:
                return
            self.doRequestUsername()

    def doLobby(self):
        """Is called when the client has successfully chosen a username on the server and 
        can now list / join / create sessions."""
        # ui updates
        self.disableGame()

        # show LobbyDialog to user that handles listing / joining / creating sessions
        # if user closes it, ask user if he wants to disconnect.
        # otherwise show again until a session was joined
        result = False
        while not result:
            dialog = LobbyDialog(self.connection, self)
            dialog.show()
            dialog.exec_()
            result = dialog.result()
            if not result:
                # connection was lost in-between
                if not self.connection:
                    return
                r = QtGui.QMessageBox.question(self, "Disconnect from server", "Do you want to disconnect from the server?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                if r == QtGui.QMessageBox.Yes:
                    self.doDisconnect()
                    return

    def onSessionJoined(self, ok, ident):
        """Is called when the client has requested to join a session and the server acknowledged that request."""
        # showing error message in case joining session was not possible is handled by lobby dialog
        if ok:
            # ui updates
            self.list.setEnabled(True)
            self.leaveSessionButton.setEnabled(True)

    def onSessionStarted(self):
        """Is called when the server has started the session."""
        # ui updates
        self.table.setEnabled(True)

    def onSudokuReceived(self, sudoku):
        """Is called when the server has updated the sudoku field."""
        # set data in ui
        self.setSudokuState(sudoku)

    def onScoresReceived(self, scores):
        """Is called when the server has updated the scores."""
        # set data in ui
        self.setScoresState(scores)

    def doSuggestNumber(self, i, j):
        """Is called when the user changed a cell in the sudoku table
        which requires sending a number suggest to the server."""
        print "Cell %d:%d changed" % (i, j)
        # get entered value, validate it
        item = self.table.item(i, j)
        x = str(item.text()).strip()
        if not x:
            return
        if x in map(str, range(1, 10)):
            x = int(x)
            print "Suggest value %d" % x
            # send suggestion to server
            self.connection.suggestNumber(i, j, x)
        else:
            print "Invalid value '%s'!" % x
        # reset value entered by user
        # block signals to not trigger another item change signal
        self.table.blockSignals(True)
        item.setText("")
        self.table.blockSignals(False)

    def onSuggestNumberAck(self, i, j, ok):
        """Is called when the server has acknowledged a number suggestion."""
        # highlight colors depending on good/bad suggestion
        red = QtGui.QBrush(QtGui.QColor.fromRgb(255, 0, 0, 128))
        green = QtGui.QBrush(QtGui.QColor.fromRgb(0, 255, 0, 128))
        color = green if ok else red

        # highlight item in sudoku table
        item = self.table.item(i, j)
        originalBg = item.background()
        # block signals otherwise change signal of item will be fired
        # and counted as edit of user
        self.table.blockSignals(True)
        item.setBackground(color)
        self.table.blockSignals(False)
        # also reset highlighting after some time
        def resetHighlight(item=item, bg=originalBg):
            self.table.blockSignals(True)
            item.setBackground(bg)
            self.table.blockSignals(False)
        QtCore.QTimer.singleShot(self.NUMBER_ACK_HIGHLIGHT_TIME, resetHighlight)
        print "Suggest number ack: %d %d -> %d" % (i, j, ok)

    def doLeaveSession(self):
        """Is called when the user requests to leave the session."""
        self.leaveSessionButton.setEnabled(False)
        # send session leave request to server and show sessions again then
        self.connection.leaveSession()
        self.doLobby()

    def onGameOver(self, winner):
        """Is called when the server announced that a game is over."""
        self.leaveSessionButton.setEnabled(False)
        # show username of the winner and show sessions again then
        QtGui.QMessageBox.information(self, "Game is over", "The game is over. Winner is: %s" % winner)
        # connection lost
        if not self.connection:
            return
        self.doLobby()

    def doDisconnect(self):
        """Is called when the user requests to disconnect from the server."""
        # TODO state
        self.disableGame()
        self.leaveSessionButton.setEnabled(False)
        # tell server connection to disconnect
        self.connection.disconnect()

    def onDisconnected(self, reason):
        """Is called when the client is disconnected from the server."""
        self.disconnectButton.setEnabled(False)

        # wait until thread is finished, destroy it then
        self.connection.wait()
        self.connection = None
        # if there is a dialog open: close it
        # will be handled as self.connection == None after it
        for widget in QtGui.QApplication.allWidgets():
            if isinstance(widget, QtGui.QDialog):
                widget.reject()
                widget.close()
        # show disconnection reason and then ask user for new server address again
        QtGui.QMessageBox.information(self, "Disconnected", "Disconnected from server:\n" + reason)
        self.doConnect()

    def setScoresState(self, scores):
        """Sets the value of the scores list."""
        self.list.clear()
        for player, points in scores:
            self.list.addItem("%s: %s points" % (player, points))

    def setSudokuState(self, sudoku):
        """Sets the value of the sudoku table."""
        # first of all: block signals so that item changes don't trigger change signals
        self.table.blockSignals(True)
        for i in range(0, 9):
            for j in range(0, 9):
                # get sudoku value at row i, column j
                # get table item at that position
                x = sudoku[i][j]
                item = self.table.item(i, j)
                # set value, make it editable if there is no number yet
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

    def disableGame(self):
        """Disables the scores list and sudoku table, and clears both."""
        self.setScoresState([])
        self.setSudokuState([[0]*9] * 9)
        self.list.setEnabled(False)
        self.table.setEnabled(False)

def sigint_handler(*args):
    sys.stderr.write("Got SIGINT, quitting...")
    QtGui.QApplication.quit()

if __name__ == "__main__":
    # create qt application, main window, run app
    signal.signal(signal.SIGINT, sigint_handler)
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
