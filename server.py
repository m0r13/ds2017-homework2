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
        self.__uuid = str(uuid.uuid4())
        self.__sudoku = Sudoku()
        self.__users = {username : 0} # username: score
    
    
    def join_game(self, username):
        __users[username] = 0
    
    def get_uuid(self):
        return __uuid
    
    def get_sudoku_state(self):
        return __sudoku.get_grid()
    
    
    def get_scores_state(self):
        return __users
        
    
    def insert_number(self, username, number, coordinate):
        point, finish = __sudoku.insert(number, coordinate)
        __users[username] += point
        
        if finish:
            #...
            pass
        
    
    def leave_game(self, username)
        score = self.__users[username]
        del self.__users[username]
        return username, score
        
        
        
class ClientThread(threading.Thread):
    
    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.__socket = client_socket
        self.__address = client_address
        self.__game = None
    
    def run(self): # Dispatch cases
        while True:
            data = read_package(__client_socket)
            if data['pkg_type'] == PKG_CREATE_SESSION:
                __game = games GAME(data['number_player'], data['username'])
                write_package(__socket, __game.get_uuid())
            elif data['pkg_type'] == PKG_GET_SESSION:
                # sessions = ...
                # write_package(__socket, sessions)
                pass
            elif data['pkg_type'] == PKG_JOIN_SESSION:
                __game.join_game(data['username'])
                # write_package(__socket, )
            elif data['pkg_type'] == PKG_LEAVE_SESSION:
                __game.leave_game(data['username'])
                # write_package(__socket, )
            elif data['pkg_type'] == PKG_SUGGEST_NUMBER:
                pass
            
            
      
    def join(self):
        __client_socket.close()
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
