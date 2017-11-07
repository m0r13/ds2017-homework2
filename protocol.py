import io
import socket
import struct

SERVER_INET_ADDR = "127.0.0.1"
SERVER_PORT = 8888
TCP_RECEIVE_BUFFER_SIZE = 1024

PKG_HELLO = 0
PKG_HELLO_ACK = 1
PKG_GET_SESSIONS = 2
PKG_JOIN_SESSION = 3
PKG_SESSION_JOINED = 4
PKG_CREATE_SESSION = 5
PKG_SESSION_STARTED = 6
PKG_SUDOKU_STATE = 7
PKG_SCORES_STATE = 8
PKG_SUGGEST_NUMBER = 9
PKG_SUGGEST_NUMBER_ACK = 10
PKG_LEAVE_SESSION = 11
PKG_GAME_OVER = 12

def read_int(stream):
    data = stream.recv(4)
    #data = stream.read(4)
    i, = struct.unpack("!i", data)
    return i

def read_bool(stream):
    return bool(read_int(stream))

def read_string(stream):
    length = read_int(stream)
    s = stream.recv(length)
    #s = stream.read(length)
    return s.decode("utf-8")

def write_int(stream, value):
    data = struct.pack("!i", value)
    stream.sendall(data)
    #stream.write(data)

def write_bool(stream, value):
    write_int(stream, int(value))

def write_string(stream, value):
    write_int(stream, len(value))
    stream.sendall(value)
    #stream.write(value)

#####

def write_hello(stream, data):
    write_int(stream, PKG_HELLO)
    write_string(stream, data["username"])

def read_hello(stream):
    data = {}
    data["username"] = read_string(stream)
    return data

#####

def write_hello_ack(stream, data):
    write_int(stream, PKG_HELLO_ACK)
    write_bool(stream, data["username_ok"])

def read_hello_ack(stream):
    data = {}
    data["username_ok"] = read_bool(stream)

#####

def write_get_sessions(stream, data):
    write_int(stream, PKG_GET_SESSIONS)

def read_get_sessions(stream):
    pass

#####

def write_sessions(stream, data):
    write_int(stream, PKG_SESSIONS)
    write_int(stream, len(data["sessions"]))
    for uuid, name, cur_num_players, max_num_players in data["sessions"]:
        write_string(stream, uuid)
        write_string(stream, name)
        write_int(stream, cur_num_players)
        write_int(stream, max_num_players)

def read_sessions(stream):
    length = read_int(stream)
    sessions = []
    for i in range(length):
        uuid = read_string(stream)
        name = read_string(stream)
        cur_num_players = read_int(stream)
        max_num_players = read_int(stream)
        sessions.append((uuid, name, cur_num_players, max_num_players))
    return {"sessions" : sessions}

#####

def write_join_session(stream, data):
    write_int(stream, PKG_JOIN_SESSION)
    write_string(stream, data["uuid"])

def read_join_session(stream):
    data = {}
    data["uuid"] = read_string(stream)
    return data

#####

def write_session_joined(stream, data):
    write_int(stream, PKG_SESSION_JOINED)
    write_bool(stream, data["ok"])
    write_string(stream, data["uuid"])

def read_session_joined(stream):
    data = {}
    data["ok"] = read_bool(stream)
    data["uuid"] = read_string(stream)
    return data

#####

def write_create_session(stream, data):
    write_int(stream, PKG_CREATE_SESSION)
    write_int(stream, data["num_players"])

def read_create_session(stream):
    data = {}
    data["num_players"] = read_int(stream)
    return data

#####

def write_session_started(stream, data):
    write_int(stream, PKG_SESSION_STARTED)

def read_session_started(stream):
    pass

#####

def write_sudoku_state(stream, data):
    write_int(stream, PKG_SUDOKU_STATE)
    assert len(data["sudoku"]) == 81
    for x in data["sudoku"]:
        write_int(stream, x)

def read_sudoku_state(stream):
    data = {}
    sudoku = []
    for i in range(81):
        sudoku.append(read_int(stream))

#####

def write_scores_state(stream, data):
    write_int(stream, PKG_SCORES_STATE)
    write_int(stream, len(data["scores"]))
    for player_name, points in data["scores"]:
        write_string(stream, player_name)
        write_int(stream, points)

def read_scores_state(stream):
    length = read_int(stream)
    scores = []
    for i in range(length):
        name = read_string(stream)
        points = read_int(stream)
        scores.append((name, points))
    return {"scores" : scores}

#####

def write_suggest_number(stream, data):
    write_int(stream, PKG_SUGGEST_NUMBER)
    write_int(stream, data["i"])
    write_int(stream, data["j"])
    write_int(stream, data["number"])

def read_suggest_number(stream):
    data = {}
    data["i"] = read_int(stream)
    data["j"] = read_int(stream)
    data["number"] = read_int(stream)
    return data

#####

def write_suggest_number_ack(stream, data):
    write_int(stream, PKG_SUGGEST_NUMBER_ACK)
    write_int(stream, data["i"])
    write_int(stream, data["j"])
    write_bool(stream, data["ok"])

def read_suggest_number_ack(stream):
    data = {}
    data["i"] = read_int(stream)
    data["j"] = read_int(stream)
    data["ok"] = read_bool(stream)

#####

def write_leave_session(stream, data):
    write_int(stream, PKG_LEAVE_SESSION)

def read_leave_session(stream):
    pass

#####

def write_game_over(stream, data):
    write_int(stream, PKG_GAME_OVER)
    write_string(stream, data["winner"])

def read_game_over(stream):
    data = {}
    data["winner"] = read_string(stream)
    return data

#####

PACKAGES = {
    PKG_HELLO : (write_hello, read_hello),
    PKG_HELLO_ACK : (write_hello_ack, read_hello_ack),
    PKG_GET_SESSIONS : (write_get_sessions, read_get_sessions),
    PKG_JOIN_SESSION : (write_join_session, read_join_session),
    PKG_SESSION_JOINED : (write_session_joined, read_session_joined),
    PKG_CREATE_SESSION : (write_create_session, read_create_session),
    PKG_SESSION_STARTED : (write_session_started, read_session_started),
    PKG_SUDOKU_STATE : (write_sudoku_state, read_sudoku_state),
    PKG_SCORES_STATE : (write_scores_state, read_scores_state),
    PKG_SUGGEST_NUMBER : (write_suggest_number, read_suggest_number),
    PKG_SUGGEST_NUMBER_ACK : (write_suggest_number_ack, read_suggest_number_ack),
    PKG_LEAVE_SESSION : (write_leave_session, read_leave_session),
    PKG_GAME_OVER : (write_game_over, read_game_over),
}

def read_package(stream):
    data = {}
    pkg_type = read_int(stream)

    assert pkg_type in PACKAGES
    data = PACKAGES[pkg_type][1](stream)

    return pkg_type, data

def write_package(stream, pkg_type, data):
    assert pkg_type in PACKAGES
    PACKAGES[pkg_type][0](data)

