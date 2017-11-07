import io
import socket
import struct

SERVER_INET_ADDR = "127.0.0.1"
SERVER_PORT = 8888
TCP_RECEIVE_BUFFER_SIZE = 1024

PKG_CREATE_SESSION = 0
PKG_JOIN_SESSION = 1
PKG_GET_SESSION = 2
PKG_LEAVE_SESSION = 3
PKG_SUGGEST_NUMBER = 4


def read_int(stream):
    #data = stream.recv(4)
    data = stream.read(4)
    i, = struct.unpack("!i", data)
    return i

def read_string(stream):
    length = read_int(stream)
    #s = stream.recv(length)
    s = stream.read(length)
    return s.decode("utf-8")

def write_int(stream, value):
    data = struct.pack("!i", value)
    #stream.sendall(data)
    stream.write(data)

def write_string(stream, value):
    write_int(stream, len(value))
    #stream.sendall(value)
    stream.write(value)

def write_create_session(stream, data):
    write_int(stream, PKG_CREATE_SESSION)
    write_int(stream, data["num_players"])

def read_create_session(stream):
    data = {}
    data["num_players"] = read_int(stream)
    return data

def write_join_session(stream, uuid):
    write_int(stream, PKG_JOIN_SESSION)
    write_int(stream, uuid)

def read_join_session(stream):
    data = {}
    data["id"] = read_int(stream)
    return data

def write_get_sessions(stream, data):
    data["sessions"] = read_string(stream)
    return data



def read_package(stream):
    data = {}
    pkg_type = read_int(stream)

    if pkg_type == PKG_CREATE_SESSION:
        data = read_create_session(stream)

    elif pkg_type == PKG_JOIN_SESSION:
        data = read_join_session(stream)

    elif pkg_type == PKG_GET_SESSION:
        data = read_get_sessions(stream)

    elif pkg_type == PKG_LEAVE_SESSION:
        pass
    elif pkg_type == PKG_SUGGEST_NUMBER:
        pass

    return pkg_type, data

def write_package(stream, data):
    pkg_type = data["pkg_type"]

    pass
