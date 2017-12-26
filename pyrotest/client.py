#!/usr/bin/env python2

import random
import Pyro4


# We need to set either a socket communication timeout,
# or use the select based server. Otherwise the daemon requestLoop
# will block indefinitely and is never able to evaluate the loopCondition.
#Pyro4.config.COMMTIMEOUT = 0.5

class SessionHandler(object):

    @Pyro4.expose
    def sessionStarted(self):
        print("handler: sessionStarted")

    @Pyro4.expose
    def sudokuChanged(self, sudoku):
        pass

    @Pyro4.expose
    def scoresChanged(self, scores):
        pass

    @Pyro4.expose
    #@Pyro4.oneway
    def gameOver(self, winner):
        print("handler: gameOver(winner='%s')" % winner)

with Pyro4.core.Daemon() as daemon:
    # register our callback handler
    callback = SessionHandler()
    daemon.register(callback)

    # contact the server and put it to work
    print("creating a bunch of workers")
    with Pyro4.core.Proxy("PYRO:sudoku@localhost:9999") as server:
        print("Got server: %s" % server)
        # can do smth like
        # server.listSessions()
        # server.createSession()
        # server.provideSessionCallback()
        # etc.
        pass

        print("Running sessions: %s" % server.listSessions())
        print("Joining session 0: %s" % server.joinSession(0))
        server.provideSessionCallback(callback)

    print("Waiting on callback...")
    daemon.requestLoop()
    #daemon.requestLoop(loopCondition=lambda: CallbackHandler.workdone < NUM_WORKERS)
