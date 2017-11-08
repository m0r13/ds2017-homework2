import socket
import time

class SocketWrapper:
    def __init__(self, socket):
        self.socket = socket
        self.buffer = bytearray("")

    def receive(self):
        try:
            d = self.socket.recv(1024)
            if d:
                self.buffer += d
            else:
                # socket is closed from other side
                # let's just fail it
                raise socket.error(32, "Broken pipe")
        except socket.error, e:
            # resource temporarily unavailable if no data in buffer (nonblocking)
            if e.errno != 11:
                raise e

    def available(self):
        return len(self.buffer)

    def recv(self, n):
        while self.available() < n:
            self.receive()
            time.sleep(0.01)
        data = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return data

    def sendall(self, data):
        self.socket.sendall(data)
