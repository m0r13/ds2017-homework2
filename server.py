#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import threading, uuid
from protocol import *
from sudoku import *
from socket import AF_INET, SOCK_STREAM, socket, SHUT_WR, SHUT_RD

class Game():
   """Represents the sudoku game on the server side.
   Creates a sudoku object and keeps track of points
   """
   
   def __init__(self, number_player, username):
        self.__number_player = number_player
        self.__session_id = str(uuid.uuid4())
        self.__sudoku = Sudoku()
        self.__users = {username : 0} # username: score
    
    
    def join_game(self, username):
        self.__users[username] = 0
    
    
    def get_sudoku_state(self):
        pass
    
    
    def get_scores_state(self):
        pass
        
    
    def insert_number(self, username, number, coordinate):
        point, finish = self.__Sudoku.insert(number, coordinate)
        self.__users[username] += point
    
    def leave_game(self, username)
        pass
       
        
        
        
class ClientThread(threading.Thread):
    
    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.__socket = client_socket
        self.__address = client_address
        
    def run(self):
        while True:
            data = read_package(self.__client_socket)
            
            # Dispatch cases to handler 
    
    
    
    
    def join(self):
        self.__client_socket.close()
        print "The client %s closed its connection" % client_address

if __name__ == '__main__':
    
    clients = []   
    
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((SERVER_INET_ADDR, SERVER_PORT))

    backlog = 0 
    s.listen(backlog)
       
    # Receive loop
    while True:
        try:
            print "Listening..."
            client_socket, client_address = s.accept()
            clients.append(ClientThread(client_socket, client_address).start())
                  
        except KeyboardInterrupt as e:
            print 'Ctrl+C issued ...'
            print 'Terminating server ...'
            break
    
    for i in clients:
        i.join()        
    
    s.close()
    print 'Closed the server socket'
    print 'Terminating ...'
