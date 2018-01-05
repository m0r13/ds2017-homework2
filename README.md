# Project for Distributed system class 2017
Implementation of a concurrent Sudoku solver using remote procedure calls and multi-cast server discovery
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
* Dialog: Server Discovery:

![Discovery](/pictures/emptydiscovery.png)

  * Reload Servers: Reload list of multicast findings 
  * Connect: Connect to selected server.

![DiscoveryFull](/pictures/fulldiscovery.png)


* Once connected: Dialog: Enter username:

![Username](/pictures/choosename.png)

  * OK: Application checks if username is valid (8 characters at most, no spaces):
  
  ![Invalid User Name](/pictures/invalidname.png)
 
  * Cancel or invalid username: Show error, valid username must be inserted, back to enter username:
  
    ![Invalid Name Error](/pictures/invalidnameerror.png)
  
* Username is sent to server. Server checks if not in use already

  * If in use already: Server sends error message, user has to enter new username:
  
      ![Name Taken](/pictures/nametaken.png)

* Lobby dialog: Running sessions are shown to the user (with name, current players, max players):

     ![Joining Session](/pictures/joiningsession.png)

* If the lobby dialog is closed by the user, the UI offers the user to disconnect from the server
* User can reload sessions
* User can create session

  * Another dialog opens, session name / max players must be entered:
  
       ![Creat Session](/pictures/createsession.png)

* User can join existing session
  * If session is already full, server sends an error message and UI is back at lobby dialog:
  
       ![Session Full](/pictures/sessionfull.png)

* When a session is joined
  * Client waits for other players and start signal of server (until then, scoreboard fills with joining players, but sudoku is visible yet). Special case when the max player count for a game is one: Start immediately, don't finish game when there is only one player left
* When session is started:

     ![Game Started](/pictures/gamestarted.png)

  * Number can be suggested by double-clicking a sudoku field and entering a number. Server acknowledges and UI highlights the cell green / red, scoreboard updates:
  
     ![Correct Input](/pictures/correctinput.png)
     
     ![Incorrect Input](/pictures/incorrectinput.png)

  * Once all fields are filled / all players except one has left, the winner is announced by the server:
     
     ![Game Over](/pictures/gameover.png)

* Back to lobby dialog then

* User can, in the session, leave the session with the button "leave session":

     ![Leaving Bottom](/pictures/gamestarted.png)

* User can, once connected to the server, disconnect from the server with the button "disconnect from server"
* If the server connection fails anywhere in-between, back to dialog where server address is entered

     ![Noconnection](/pictures/connect.png)

