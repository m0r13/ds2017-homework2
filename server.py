#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import threading, uuid
from protocol import *
from sudoku import *
from socket import AF_INET, SOCK_STREAM, socket

class Manager():
    """Contains the global variables for the server,
    acts as manager and is passed to all Threads"""
    
    def __init__(self):
        self.ServerGames = {}
        self.clients = []
        self.ServerUsernames = [] 
    
    def notify(self, game, username):
        for i in clients:
            if game.get_uuid() == i.game.get_uuid():
                write_package(i.socket, PKG_SUDOKU_STATE, \
                              {'sudoku': game.get_sudoku().serialize()})
                write_package(i.socket, PKG_SCORES_STATE, {'scores': game.get_scores()})
        
    def game_over(self, game):
        for i in clients:
            if game.get_uuid() == i.game.get_uuid():
                write_package(i.socket, PKG_GAME_OVER, {'winner': True})
        print "Game over, game uuid: %s" % game.get_uuid()
                 
    def remove_client(self, username):
        for i in range(0, len(self.clients)):
            if self.clients[i].username == username:
                del self.clients[i]  
             
class Game():
    """Represents the sudoku game on the server side.
    Creates a sudoku object and keeps track of points
    """
    
    def __init__(self, num_players, username):
        self.__num_players = num_players
        self.__uuid = str(uuid.uuid4())
        self.__sudoku = Sudoku()
        self.__users = {username : 0} # username: score
        self.__game_name = username + "'s game"
    
    def join(self, username):
        assert(not self.is_full(game))
        self.__users[username] = 0

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

    def is_full(self):
        return len(self.__users) == self.__num_players
        
    def insert_number(self, username, i, j, number):
        point, finish = self.__sudoku.insert(i, j, number)
        self.__users[username] += point
        return point, finish
        
    def leave_game(self, username):
        del self.__users[username]
        return self.get_cur_num_players() == 1

    def get_game_name(self):    
        return self.__game_name

class ClientThread(threading.Thread):
    
    def __init__(self, client_socket, client_address, manager):
        threading.Thread.__init__(self)
        self.username = None
        self.socket = client_socket
        self.address = client_address
        self.game = None
    
    def run(self): # Dispatch cases
        finish = False 
        while True:
            
            # Read incoming packet
            pkg_type, data = read_package(self.socket)
            
            # Connection
            if pkg_type == PKG_HELLO:
                if data['username'] not in manager.ServerUsernames:
                    print "Received PKG_HELLO"
                    manager.ServerUsernames.append(data['username'])
                    self.username = data['username']
                    write_package(self.socket, PKG_HELLO_ACK, {'ok' : True})
                else:
                    write_package(self.socket, PKG_HELLO_ACK, {'ok' : False})
            
            # Get list of sessions
            elif pkg_type == PKG_GET_SESSIONS:
                print "Received PKG_GET_SESSIONS"
                out = {'sessions': []}
                for i in manager.ServerGames.keys():
                    game = manager.ServerGames[i]
                    out['sessions'].append((i, game.get_game_name(), game.get_cur_num_players(), game.get_num_players())) 
                write_package(self.socket, PKG_SESSIONS, out)
            
            # Join existing session   
            elif pkg_type == PKG_JOIN_SESSION:
                print "Received PKG_JOIN_SESSION"
                if game.isFull(manager.ServerGames[data['uuid']]) \
                or data['uuid'] not in manager.ServerGames:
                    write_package(self.socket, PKG_SESSION_JOINED, {'ok' : False, 'uuid' : data['uuid']})
                else:
                    game = manager.ServerGames[data['uuid']]
                    game.join(self.username)
                    write_package(self.socket, PKG_SESSION_JOINED, {'ok' : True, 'uuid' : data['uuid']})
                    write_package(self.socket, PKG_SESSION_STARTED, {})             
                    write_package(self.socket, PKG_SUDOKU_STATE, \
                                  {'sudoku': game.get_sudoku().serialize()})
                    write_package(self.socket, PKG_SCORES_STATE, {'scores': game.get_scores()})
                        
                    
            # Create new session   
            elif pkg_type == PKG_CREATE_SESSION:
                print "Received PKG_CREATE_SESSION"
                self.game = Game(data['num_players'], self.username)
                manager.ServerGames[self.game.get_uuid()] = self.game
                write_package(self.socket, PKG_SESSION_JOINED, \
                              {'ok' : True, 'uuid' : self.game.get_uuid()})           
                write_package(self.socket, PKG_SESSION_STARTED, {})             
                write_package(self.socket, PKG_SUDOKU_STATE, \
                              {'sudoku': self.game.get_sudoku().serialize()})
                write_package(self.socket, PKG_SCORES_STATE, {'scores': self.game.get_scores()})
            
            # Player suggest a number
            elif pkg_type == PKG_SUGGEST_NUMBER:
                print "Received PKG_SUGGEST_NUMBER"
                point, finish = self.game.insert_number(self.username, data['i'], data['j'], data['number'])
                write_package(self.socket, PKG_SUGGEST_NUMBER_ACK, \
                              {'ok' : True, 'i' : data['i'], 'j' : data['j']})
                
                # Notify to everyone in the same game
                manager.notify(game)
                print "%s wrote %d in position (%d, %d) in the Sudoku with game uuid %s" % \
                      (username, data['number'], data['i'], data['j'], self.game.get_uuid())
                      
            # Player wants to leave
            elif pkg_type == PKG_LEAVE_SESSION:
                print "Received PKG_LEAVE_SESSION"
                finish = self.game.leave_game(self.username)

            
            if finish:
                manager.game_over(self.game)
        

if __name__ == '__main__':
    manager = Manager()
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((SERVER_INET_ADDR, SERVER_PORT))

    backlog = 0 
    s.listen(backlog)
       
    # Receive loop
    while True:
        try:
            print "Listening..."
            client_socket, client_address = s.accept()
            client_thread = ClientThread(client_socket, client_address, manager)
            client_thread.start()
            print "New client connected"
            manager.clients.append(client_thread)
        
        except KeyboardInterrupt as e:
            print 'Ctrl+C issued ...'
            print 'Terminating server ...'
            break
    
    for i in manager.clients:
        i.join()        
        client_socket.close()
        manager.remove_client(i.username)
        print "The client %s closed its connection" % str(client_address)
    s.close()
    print 'Closed the server socket'
    print 'Terminating ...'
