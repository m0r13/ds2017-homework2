#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import threading
from protocol import *
from socket import AF_INET, SOCK_STREAM, socket, SHUT_WR, SHUT_RD

class ClientThread(threading.Thread):
    
    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.socket = client_socket
        self.address = client_address
        
    def run(self):
        while True:
            data = read_package(client_socket)
            
            # Dispatch cases to handler 
    
    def create_session(self):
        pass
        # ...        
    
    def remove_session(self):
        pass
        # ... 
    
    
    def join(self):
        client_socket.close()
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
