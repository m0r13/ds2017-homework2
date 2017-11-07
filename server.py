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
   
   def __init__(self, num_players, username):
        self.__num_players = num_players
        self.__uuid = str(uuid.uuid4())
        self.__sudoku = Sudoku()
        self.__users = {username : 0} # username: score
    
    @staticmethod
    def join_game(game, username):
        assert(!isFull(game))
        game.__users[username] = 0
        
    
    def get_uuid(self):
        return self.__uuid
    
    def get_sudoku(self):
        return self.__sudoku
    
    
    def get_scores(self):
        return self.__users.items() # convert dict to array of tuples
    
    def get_num_players(self):
        return self.__num_players    
    
    def get_cur_num_players(self):
        return len(self.__users)
        
    def insert_number(self, username, i, j, number):
        point, finish = self.__sudoku.insert(i, j, number)
        self.__users[username] += point
        
        if finish:
            #...
            pass
    
    
    # returns True if there are num_player users in the game
    @staticmethod
    def isFull(game)
        return len(game.__users)==game.__num_players    
    
    
    def leave_game(self, username)
        score = self.__users[username]
        del self.__users[username]
        return username, score
        
        
        
class ClientThread(threading.Thread):
    
    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.__username = None
        self.__socket = client_socket
        self.__address = client_address
        self.__game = None
    
    def run(self): # Dispatch cases
        
        while True:
            
            # Read incoming packet
            pkg_type, data = read_package(__client_socket)
            
            # Connection
            if pkg_type == PKG_HELLO:
                if data['username'] not in ServerUsernames:
                    ServerUsernames.append(data['username'])
                    self.__username = data['username']
                    write_package(__socket, PKG_HELLO_ACK, {'username_available' : True})
                else:
                    write_package(__socket, PKG_HELLO_ACK, {'username_available' : False})
            
            # Get list of sessions
            elif pkg_type == PKG_GET_SESSION:
                out = {'sessions': []}
                for i in ServerGames.keys():
                    out['sessions'].append((i, Servergames[i].get_cur_num_players())) 
                write_package(__socket, PKG_SESSIONS, out)
            
            # Join existing session   
            elif pkg_type == PKG_JOIN_SESSION:
                if Game.isFull(Servergames[data['uuid']]) or data['uuid'] not in Servergames:
                    write_package(__socket, PKG_SESSION_JOINED, {'ok' : False, 'uuid' : data['uuid']})
                else:
                    __game = Servergames[data['uuid']]
                    Game.join_game(Servergames[data['uuid']], self.__username)
                    write_package(__socket, PKG_SESSION_JOINED, {'ok' : True, 'uuid' : data['uuid']})
                    write_package(__socket, PKG_SESSION_STARTED, {})             
                    write_package(__socket, PKG_SUDOKU_STATE, {'sudoku': __game.get_sudoku().serialize()})
                    write_package(__socket, PKG_SCORES_STATE, {'scores': __game.get_scores()})
                        
                    
            # Create new session   
            elif pkg_type == PKG_CREATE_SESSION:
                self.__game = Game(data['num_players'], self.__username)
                ServerGames[self.__game.get_uuid()] = self.__game
                write_package(self.__socket, PKG_SESSION_JOINED, {'ok' : True, 'uuid' : self.__game.get_uuid())
                write_package(self.__socket, PKG_SESSION_STARTED, {})             
                write_package(self.__socket, PKG_SUDOKU_STATE, {'sudoku': self.__game.get_sudoku().serialize()})
                write_package(self.__socket, PKG_SCORES_STATE, {'scores': self.__game.get_scores()})
            
            # Player suggest a number
            elif pkg_type == PKG_SUGGEST_NUMBER:
                self.__game.insert_number(self.__username, data['i'], data['j'], data['number']):
                write_package(self.__socket, PKG_SUGGEST_NUMBER_ACK, {'ok' : True, 'i' : data['i'], 'j' : data['j'])
                write_package(self.__socket, PKG_SUDOKU_STATE, {'sudoku': self.__game.get_sudoku().serialize()})
                write_package(self.__socket, PKG_SCORES_STATE, {'scores': self.__game.get_scores()})
                
                
               
            # Player wants to leave
            elif pkg_type == PKG_LEAVE_SESSION:
                self.__game.leave_game(self.__username)

            
            
            
      
    def join(self):
        __client_socket.close()
        print "The client %s closed its connection" % client_address

if __name__ == '__main__':
    ServerGames={}
    clients = []
    ServerUsernames=[]  
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
