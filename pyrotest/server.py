#!/usr/bin/env python2

import time
import threading
import Pyro4

def get_id():
    peer = Pyro4.current_context.client_sock_addr
    ip = Pyro4.socketutil.getIpAddress(peer[0], workaround127=True)
    return "%s:%d" % (ip, peer[1])

class SudokuServer(object):
    def __init__(self):
        pass

    @Pyro4.expose
    def listSessions(self):
        return [0, 1, 2]

    @Pyro4.expose
    def createSession(self, name, num_players):
        pass

    @Pyro4.expose
    def joinSession(self, session):
        return True

    @Pyro4.expose
    def provideSessionCallback(self, callback):
        # check if he's really in session... blah
        # register callback for server
        # it can be used later to notify the client about session changes
        # see client.py SessionHandler
        
        # smth like
        # self.client_callbacks[get_id()] = callback

        print("Got client callback: %s" % callback)
        def answer(callback=callback):
            #callback.sessionStarted()
            time.sleep(1)
            print("Sending game over!")
            callback.gameOver("You!")
            time.sleep(5)
            callback.gameOver("Test")
        threading.Thread(target=answer).start()

    @Pyro4.expose
    def suggestNumber(self, i, j, value):
        pass

Pyro4.Daemon.serveSimple({
    SudokuServer(): "sudoku"
}, host="localhost", port=9999, ns=False)
