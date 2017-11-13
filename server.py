#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
usage: server.py [-h] [-v] [-H HOST] [-p PORT]

Concurrent Sudoku

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -H HOST, --host HOST  Server TCP port, defaults to 127.0.0.1
  -p PORT, --port PORT  Server TCP port, defaults to 8888
"""

import time, threading, uuid, util
from protocol import *
from sudoku import *
from socket import AF_INET, SOCK_STREAM, SHUT_WR, socket
from argparse import ArgumentParser # Parsing command line arguments

class Manager():
    """Contains the global variables for the server,
    acts as manager and is passed to all Threads"""
    
    def __init__(self):
        self.ServerGames = {}
        self.clients = []
        self.ServerUsernames = [] 
        print "Created manager"
    
    def notify(self, game):
        for i in self.clients:
            if game.get_uuid() == i.game.get_uuid():
                write_package(i.socket, PKG_SUDOKU_STATE, \
                              {'sudoku': game.get_sudoku().serialize()})
                write_package(i.socket, PKG_SCORES_STATE, {'scores': game.get_scores()})
        
    def game_over(self, game):
        for i in self.clients:
            if game.get_uuid() == i.game.get_uuid():
                write_package(i.socket, PKG_GAME_OVER, {'winner': game.get_scores()[0][0]})
        print "Game over, game uuid: %s" % game.get_uuid()
                 
    def remove_client(self, username):
        for i in range(0, len(self.clients)):
            if self.clients[i].username == username:
                del self.clients[i]
    
    def start_game(self, game):
        for i in self.clients:
            if game.get_uuid() == i.game.get_uuid():
                write_package(i.socket, PKG_SESSION_STARTED, {})
        print "Game over, game uuid: %s" % game.get_uuid()
             
class Game():
    """Represents the sudoku game on the server side.
    Creates a sudoku object and keeps track of points
    """
    
    def __init__(self, name, num_players, username):
        self.__num_players = num_players
        self.__uuid = str(uuid.uuid4())
        self.__sudoku = Sudoku()
        self.__users = {username : 0} # username: score
        self.__game_name = name
        print "New game '%s' created by user '%s', with max %d users and uuid %s" % \
              (name, username, num_players, self.__uuid)
    
    def join(self, username):
        assert(not self.is_full())
        self.__users[username] = 0

    def get_uuid(self):
        return self.__uuid

    def get_sudoku(self):
        return self.__sudoku

    def get_scores(self):
        return sorted(self.__users.items(), key = lambda i: i[1]) # convert dict to array of tuples

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
        self.socket.setblocking(False)
        self.address = client_address
        self.game = None
        self.should_stop = False
    
    def run(self): # Dispatch cases
        finish = False 
        try:
            stream = util.SocketWrapper(self.socket)
            while not self.should_stop:
                stream.receive()
                if not stream.available():
                    time.sleep(0.01)
                    continue
                
                # Read incoming packet
                pkg_type, data = read_package(stream)
                
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
                        self.game = manager.ServerGames[i]
                        out['sessions'].append( \
                        (i, self.game.get_game_name(), self.game.get_cur_num_players(),\
                         self.game.get_num_players())) 
                    write_package(self.socket, PKG_SESSIONS, out)
                
                # Join existing session   
                elif pkg_type == PKG_JOIN_SESSION:
                    print "Received PKG_JOIN_SESSION"
                    if data['uuid'] not in manager.ServerGames \
                    or manager.ServerGames[data['uuid']].is_full():
                        write_package(self.socket, PKG_SESSION_JOINED, \
                                      {'ok' : False, 'uuid' : data['uuid']})
                    else:
                        self.game = manager.ServerGames[data['uuid']]
                        self.game.join(self.username)
                        write_package(self.socket, PKG_SESSION_JOINED, \
                                      {'ok' : True, 'uuid' : data['uuid']}) 
                        
                        if self.game.is_full():
                            manager.start_game(self.game) 
                                      
                        write_package(self.socket, PKG_SUDOKU_STATE, \
                                      {'sudoku': self.game.get_sudoku().serialize()})
                        write_package(self.socket, PKG_SCORES_STATE, {'scores': self.game.get_scores()})      
                        
                # Create new session   
                elif pkg_type == PKG_CREATE_SESSION:
                    print "Received PKG_CREATE_SESSION"
                    self.game = Game(data['name'], data['num_players'], self.username)
                    manager.ServerGames[self.game.get_uuid()] = self.game
                    write_package(self.socket, PKG_SESSION_JOINED, \
                                  {'ok' : True, 'uuid' : self.game.get_uuid()})
                    if self.game.is_full():
                        manager.start_game(self.game)                       
                    write_package(self.socket, PKG_SUDOKU_STATE, \
                                  {'sudoku': self.game.get_sudoku().serialize()})
                    write_package(self.socket, PKG_SCORES_STATE, {'scores': self.game.get_scores()})
                    
                    
                # Player suggest a number
                elif pkg_type == PKG_SUGGEST_NUMBER:

                    print "Received PKG_SUGGEST_NUMBER"
                    point, finish = self.game.insert_number(self.username, data['i'], \
                                                            data['j'], data['number'])
                    write_package(self.socket, PKG_SUGGEST_NUMBER_ACK, \
                                  {'ok' : point > 0, 'i' : data['i'], 'j' : data['j']})
                    
                    # Notify to everyone in the same game
                    manager.notify(self.game)
                    print "%s wrote %d in position (%d, %d) in the Sudoku with game uuid %s" % \
                          (self.username, data['number'], data['i'], data['j'], self.game.get_uuid())
                          
                # Player wants to leave
                elif pkg_type == PKG_LEAVE_SESSION:
                    print "Received PKG_LEAVE_SESSION"
                    finish = self.game.leave_game(self.username)

                if finish:
                    manager.game_over(self.game)

            self.socket.shutdown(SHUT_WR)
            self.socket.close()
        
        except Exception, msg:
            print "Exception: %s" % msg
    
    def stop(self):
        self.should_stop = True


if __name__ == '__main__':
    
    # Parse args
    parser = ArgumentParser(description="Concurrent Sudoku", version = "1.0")
    parser.add_argument('-H','--host', help='Server TCP port, '\
                        'defaults to %s' % SERVER_INET_ADDR, \
                        default=SERVER_INET_ADDR)
    parser.add_argument('-p','--port', type=int, help='Server TCP port, '\
                        'defaults to %d' % SERVER_PORT, default=SERVER_PORT)
    args = parser.parse_args()
    
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
        except Exception, msg:
            print 'Exception %s' % msg
            
    for i in manager.clients:
        i.stop()
        i.join()        
        manager.remove_client(i.username)
        print "The client %s closed its connection" % str(client_address)
    s.close()
    print 'Closed the server socket'
    print 'Terminating ...'
