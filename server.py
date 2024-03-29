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
  -M MULTICAST_IP, --mcip MCIP  Multicast IP, defaults 239.1.1.1
  -o MULTICAST_PORT, --mcport MCPORT  Multicast port, defaults to 7778
"""

import time, threading, uuid, util                          # Miscellaneous utils
from protocol import *                                      # Import our own protocol class
from sudoku import *                                        # Import our own sudoku class
from argparse import ArgumentParser                         # Parsing command line arguments
from socket import AF_INET, SOCK_DGRAM, IPPROTO_IP, IP_MULTICAST_LOOP, IP_MULTICAST_TTL, socket
import traceback, Pyro4

def get_id():
    peer = Pyro4.current_context.client_sock_addr
    ip = Pyro4.socketutil.getIpAddress(peer[0], workaround127=True)
    return "%s:%d" % (ip, peer[1])


def send_multicast(rpc_addr, mc_addr,ttl=1):
    MSG = MULTICAST_MSG + MSG_FIELD_SEP + ('%s:%d' % rpc_addr)
    try:
        s = socket(AF_INET, SOCK_DGRAM)
        print 'UDP socket declared'
        s.setsockopt(IPPROTO_IP, IP_MULTICAST_LOOP, 1)
        print 'Enabled loop-back multi-casts ...'

        if s.getsockopt(IPPROTO_IP, IP_MULTICAST_TTL) != ttl:
            s.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl)
            print 'Set multicast message to %d' % ttl

        while True:
            s.sendto(MSG, mc_addr)
            print 'Multicast sent to [%s:%d]: %s' % (mc_addr + (MSG,))
            time.sleep(5)

        sock_addr = s.getsockname()
        s.close()
        print 'Closed multicast sending socket %s:%d' % sock_addr
    except Exception as e:
        print 'Can not send MC request: %s' % str(e)


manager = None

class Manager():
    """Contains the global variables for the server,
    acts as manager and is passed to all Threads"""

    def __init__(self):
        """Manager constructor, shared variables for the threads"""
        self.ServerGames = {}
        self.ServerUsernames = []
        self.client_callbacks = {}
        print "Created manager"

    def notify_score(self, game):
        """ Notify all users in the same game about the scores"""
        for i in game.users.keys():
            self.client_callbacks[i].scoresChanged(game.get_scores())

    def notify(self, game):
        """ Notify all users in the same game about the changes in the sudoku"""
        for i in game.users.keys():
            self.client_callbacks[i].sudokuChanged(game.get_sudoku().serialize())
            self.client_callbacks[i].scoresChanged(game.get_scores())

    def game_over(self, game):
        """ Notify all users in the same game when game is over"""

        for i in game.users.keys():
            self.client_callbacks[i].gameOver(game.get_scores()[0][0])
        self.ServerGames.remove(game.get_uuid())
        print "Game over, game uuid: %s" % game.get_uuid()


    def remove_client(self, username):
        """Remove client from game"""
        self.client_callbacks.remove(username)
        self.ServerUsernames.remove(username)

    def start_game(self, game):
        """Send the start packet, used when game is full of players"""
        for i in game.users.keys():
            self.client_callbacks[i].sessionStarted()
        print "Game starting, game uuid: %s" % game.get_uuid()


class Game():
    """Represents the sudoku game on the server side.
    Creates a sudoku object and keeps track of points"""

    def __init__(self, name, num_players, username):
        """Game constructor, initialize Sudoku game and its needed variables"""
        self.__num_players = num_players
        self.__uuid = str(uuid.uuid4())
        self.__sudoku = Sudoku()
        self.users = {username : 0} # username: score
        self.__game_name = name
        print "New game '%s' created by user '%s', with max %d users and uuid %s" % \
              (name, username, num_players, self.__uuid)

    def join(self, username):
        """Used to make a new user join the game"""
        assert(not self.is_full())
        self.users[username] = 0

    def get_uuid(self):
        """Returns the unique identifier of the game"""
        return self.__uuid

    def get_sudoku(self):
        """Returns the Sudoku object of the game"""
        return self.__sudoku

    def get_scores(self):
        """Returns an array tuples of the users with their score.
        Sorted from winner to loser (big to small score)"""
        return sorted(self.users.items(), key = lambda i: i[1]) # convert dict to array of tuples

    def get_num_players(self):
        """Returns the maximal number of players in this game"""
        return self.__num_players

    def get_cur_num_players(self):
        """Returns the current number of players in this game"""
        return len(self.users)

    def is_full(self):
        """Returns true if current number of players == maximal number of players"""
        return len(self.users) == self.__num_players

    def insert_number(self, username, i, j, number):
        """Used to insert a number in the Sudoku grid, returns:
             1  if valid
             0  if already in the grid
            -1  if not valid
        Updates the users points and also returns True if game is finished"""
        point, finish = self.__sudoku.insert(i, j, number)
        self.users[username] += point
        return point, finish

    def leave_game(self, username):
        """Used to leave the game, returns True if only 1 player left"""
        del self.users[username]
        if len(self.users) < 1:
            del manager.ServerGames[self.get_uuid()]
        return self.get_cur_num_players() == 1

    def get_game_name(self):
        """Returns the given name for a game"""
        return self.__game_name


class SudokuServer(object):
    def __init__(self):
        self.username = None
        self.callback = None
        self.game = None

    @Pyro4.expose
    def setUsername(self, username):
        print("Pyro SudokuServer.setUsername")
        if username in manager.ServerUsernames:
            return False
        else:
            self.username = username
            manager.client_callbacks[self.username] = self.callback
            manager.ServerUsernames.append(username)
            return True

    @Pyro4.expose
    def listSessions(self):
        print("Pyro SudokuServer.listSessions")
        result = []
        for i in manager.ServerGames.keys():
            self.game = manager.ServerGames[i]
            result.append( \
            (i, self.game.get_game_name(), self.game.get_cur_num_players(),\
             self.game.get_num_players()))
        return result

    @Pyro4.expose
    def createSession(self, name, num_players):
        print("Pyro SudokuServer.createSession")
        self.game = Game(name, num_players, self.username)
        manager.ServerGames[self.game.get_uuid()] = self.game
        if self.game.is_full():
            manager.start_game(self.game)
            manager.notify(self.game)
        else:
            manager.notify_score(self.game)
        return 

    @Pyro4.expose
    def joinSession(self, session):
        if session not in manager.ServerGames:
            return False

        game = manager.ServerGames[session]
        if game.is_full():
            return False
        else:
            self.game = game
            self.game.join(self.username)
            if self.game.is_full():
                manager.start_game(self.game)
                manager.notify(self.game)
            else:
                manager.notify_score(self.game)
            return True

    @Pyro4.expose
    def provideSessionCallback(self, callback):
        # check if he's really in session... blah
        # register callback for server
        # it can be used later to notify the client about session changes
        # see client.py SessionHandler

        # smth like
        # self.client_callbacks[get_id()] = callback

        self.callback = callback
        print("Got client callback: %s" % callback)

    @Pyro4.expose
    def suggestNumber(self, i, j, value):
        point, finish = self.game.insert_number(self.username, i, j, value)

        # Notify to everyone in the same game
        manager.notify(self.game)
        print "%s wrote %d in position (%d, %d) in the Sudoku with game uuid %s" % \
              (self.username, value, i, j, self.game.get_uuid())
        if finish:
            manager.game_over(self.game)
        return i, j, point

    @Pyro4.expose
    def leaveSession(self):
        finish = self.game.leave_game(self.username)
        if finish:
            manager.game_over(self.game)
        return


if __name__ == '__main__':
    """Server entry point"""

    # Parse args
    parser = ArgumentParser(description="Concurrent Sudoku", version = "1.0")
    parser.add_argument('-H','--host', help='Server TCP port, '\
                        'defaults to %s' % SERVER_INET_ADDR, \
                        default=SERVER_INET_ADDR)
    parser.add_argument('-p','--port', type=int, help='Server TCP port, '\
                        'defaults to %d' % SERVER_PORT, default=SERVER_PORT)
    parser.add_argument('-M','--mcip', help='Multicast IP, '\
                        'defaults to %s' % MULTICAST_IP, \
                        default=MULTICAST_IP)
    parser.add_argument('-o','--mcport', type=int, help='Multicast port, '\
                        'defaults to %d' % MULTICAST_PORT, default=MULTICAST_PORT)
    args = parser.parse_args()

    # Create Manager
    manager = Manager()

    # Send multicast
    sender = threading.Thread(target=send_multicast, args=((args.host, args.port), (args.mcip, args.mcport)), kwargs={})
    sender.daemon = True
    sender.start()

    Pyro4.Daemon.serveSimple({
        SudokuServer: "sudoku"
    }, host=args.host, port=args.port, ns=False)
