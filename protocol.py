import io
import socket
import struct

# some constants
SERVER_INET_ADDR = "127.0.0.1"
SERVER_PORT = 8888
TCP_RECEIVE_BUFFER_SIZE = 1024

# types of packages
PKG_HELLO = 0
PKG_HELLO_ACK = 1
PKG_GET_SESSIONS = 2
PKG_SESSIONS = 3
PKG_JOIN_SESSION = 4
PKG_SESSION_JOINED = 5
PKG_CREATE_SESSION = 6
PKG_SESSION_STARTED = 7
PKG_SUDOKU_STATE = 8
PKG_SCORES_STATE = 9
PKG_SUGGEST_NUMBER = 10
PKG_SUGGEST_NUMBER_ACK = 11
PKG_LEAVE_SESSION = 12
PKG_GAME_OVER = 13

def read_bytes(stream, n):
    """Reads exactly n bytes from a stream.
    Blocks until all bytes are read and then returns them."""
    data = bytes()
    while len(data) != n:
        d = stream.recv(n - len(data))
        if d:
            data = data + d
    return data

def read_int(stream):
    """Reads a 4-byte integer (network byte order) from a stream."""
    data = read_bytes(stream, 4)
    i, = struct.unpack("!i", data)
    return i

def read_bool(stream):
    """Reads a boolean from a stream. It is encoded as an integer (value 0 or 1)."""
    return bool(read_int(stream))

def read_string(stream):
    """Reads a string from a stream. It is encoded as length (integer)
    followed by length number of characters."""
    length = read_int(stream)
    s = read_bytes(stream, length)
    return s.decode("utf-8")

def write_int(stream, value):
    """Writes an integer analogous to the read_int method."""
    data = struct.pack("!i", value)
    stream.sendall(data)

def write_bool(stream, value):
    """Writes a boolean analogous to the read_bool method."""
    write_int(stream, int(value))

def write_string(stream, value):
    """Writes a string analogous to the read_string method."""
    write_int(stream, len(value))
    stream.sendall(value)

"""Following functions define the different packages being used.
For each package there is a read and a write method.

The write method gets a stream and a data dictionary with package fields passed.
It is also possible to use the generic write_package method with
a package type id and data dictionary.

The read method gets a stream to read from passed. Do not use the
read methods manually, instead see read_package below."""

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
    write_bool(stream, data["ok"])

def read_hello_ack(stream):
    data = {}
    data["ok"] = read_bool(stream)
    return data

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
    write_string(stream, data["name"])
    write_int(stream, data["num_players"])

def read_create_session(stream):
    data = {}
    data["name"] = read_string(stream)
    data["num_players"] = read_int(stream)
    return data

#####

def write_session_started(stream, data):
    write_int(stream, PKG_SESSION_STARTED)

def read_session_started(stream):
    return {}

#####

def write_sudoku_state(stream, data):
    write_int(stream, PKG_SUDOKU_STATE)
    assert len(data["sudoku"]) == 81
    for x in data["sudoku"]:
        write_int(stream, x)

def read_sudoku_state(stream):
    sudoku = []
    for i in range(81):
        sudoku.append(read_int(stream))
    return {"sudoku" : sudoku}

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
    return data

#####

def write_leave_session(stream, data):
    write_int(stream, PKG_LEAVE_SESSION)

def read_leave_session(stream):
    return {}

#####

def write_game_over(stream, data):
    write_int(stream, PKG_GAME_OVER)
    write_string(stream, data["winner"])

def read_game_over(stream):
    data = {}
    data["winner"] = read_string(stream)
    return data

#####

"""
Associations of read/write methods of packages to package ids.
"""
PACKAGES = {
    PKG_HELLO : (write_hello, read_hello),
    PKG_HELLO_ACK : (write_hello_ack, read_hello_ack),
    PKG_GET_SESSIONS : (write_get_sessions, read_get_sessions),
    PKG_SESSIONS : (write_sessions, read_sessions),
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
    """Reads a package from a stream.
    First reads the package type and then uses the according
    read method of the package type to parse the payload.
    Returns a tuple (package type id, data dictionary)."""

    data = {}
    pkg_type = read_int(stream)

    assert pkg_type in PACKAGES
    data = PACKAGES[pkg_type][1](stream)

    return pkg_type, data

def write_package(stream, pkg_type, data):
    """Writes a package (with package type id and data dictionary) to a stream.
    Works analogous to the read_package method, just that package write
    methods handle writing the package type id."""
    assert pkg_type in PACKAGES
    PACKAGES[pkg_type][0](stream, data)

