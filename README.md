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
