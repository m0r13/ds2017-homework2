# Project for Distributed system class 2017
Implementation of a concurrent Sudoku solver
## Students
- Shahla Atapoor
- Sander Mikelsaar
- Moritz Hilscher
- Bruno Produit

## Instructions
- Requires module [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download) for the client GUI
```
apt-get install python-qt4
```
- Run server: 
```
server.py [-h] [-v] [-H HOST] [-p PORT]

Concurrent Sudoku

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -H HOST, --host HOST  Server TCP port, defaults to 127.0.0.1
  -p PORT, --port PORT  Server TCP port, defaults to 8888
```
 
- Run client: 
```
python client.py
```

## Client User Interface documentation

Use Cases:

* Open Application
* Dialog: Enter server address
  * OK: Connect to server
  * Cancel: Terminate application.
* If connection to server fails: Show error, go back to enter server address
* Once connected: Dialog: Enter username
  * OK: Application checks if username is valid (8 characters at most, no spaces)
  * Cancel or invalid username: Show error, valid username must be inserted, back to enter username
* Username is sent to server. Server checks if not in use already
  * If in use already: Server sends error message, user has to enter new username
* Lobby dialog: Running sessions are shown to the user (with name, current players, max players)
* User can reload sessions
* User can create session
  * Another dialog opens, session name / max players must be entered
* User can join existing session
  * If session is already full, server sends an error message and UI is back at lobby dialog
* When a session is joined:
  * Client waits for other players and start signal of server (until then, scoreboard fills with joining players, but sudoku is visible yet). Special case when the max player count for a game is one: Start immediately, don't finish game when there is only one player left
* When session is started:
  * Number can be suggested by double-clicking a sudoku field and entering a number. Server acknowledges and UI highlights the cell green / red, scoreboard updates
  * Once all fields are filled / all players except one has left, the winner is announced by the server
* Back to lobby dialog then

* User can, in the session, leave the session with the button "leave session"
* User can, once connected to the server, disconnect from the server with the button "disconnect from server"
* If the server connection fails anywhere in-between, back to dialog where server address is entered
