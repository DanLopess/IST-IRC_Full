import sys
import os
import time
import socket
import threading
import random
import fileinput
import signal
sys.path.insert(0, 'src/')
from server_module import *
from PlayerServer import handleRequest
from ScoreServer import handleRequest
from MasterServer import handleRequest

# **************************************************************************************
#
#                         IRC PROJECT - GAME SERVER
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
#
#           NOTE: ALL DEFINITIONS AND MESSAGES TYPES ARE IN SERVER_MODULE (import)
#
# Project source files: server.py , src/server_module.py , src/ScoreServer.py, src/MasterServer.py
# src/PlayerServer.py, clients/master.py, clients/score.py, clients/player.py
# **************************************************************************************

# ************** socket communication parameters ******************
bind_ip = '127.0.0.1'
bind_port = 12345
MSG_SIZE = 1024

# ******************** generic functions ********************
def signal_handler(sig, frame):
    print('You pressed Ctrl+C. Leaving...')
    server.close()  # close socket
    for i in threads:  # waits for all threads to finish, avoids corruption of data
        i.join()
    sys.exit(0)  # if multiple threads, must receive command twice

def handle_client_connection(client_socket, address):
    msg_from_client = client_socket.recv(MSG_SIZE)
    request = msg_from_client.decode()
    message = request.split(':')
    type = 0

    if (len(message) > 1 and message[COMMAND] == LOG):
        if (message[COMMAND+1] == MSTR):
            type = 1 # type 1 = master
            active_users.append(client_sock)
            msg_to_client = OK + LOG_OK
        elif (message[COMMAND+1] == SCR):
            type = 2 # type 2 = score
            active_users.append(client_sock)
            msg_to_client = OK + LOG_OK
        elif (message[COMMAND+1] == PLR):
            type = 3 # type 3 = player
            msg_to_client = OK + LOG_OK
            active_users.append(client_sock)
        else: 
            msg_to_client = NOK + INV_MSG
        
        client_socket.send(msg_to_client.encode())

        #after type assignment, enters loop
        while True:
            msg_from_client = client_socket.recv(MSG_SIZE)
            request = msg_from_client.decode()

            print('Received {} from {} , {}'.format(
                request, address[IP], address[PORT]))

            # Splits input message by its separation punctuation (:)
            message = request.split(":")

            if (len(message) == 1 and message[COMMAND] == LOGOUT):  # LOGOUT
                break
            else:
                msg_to_client = execute_command(message, type, address)

            client_socket.send(msg_to_client.encode())
    else:
        msg_to_client = NOK + LOG_NOK
        client_socket.send(msg_to_client.encode())

    # end of connection
    client_socket.close()
    active_users.remove(client_socket)
    threads.remove(threading.current_thread())

def generate_save():
    # creates game map
    if not os.path.exists(MAP):
        with open(MAP, "w") as fn:
            for i in range(0, 5):
                for f in range(0, 5):
                    fn.write(
                        str((i, f))+" ; PLAYERS: NULL; FOOD: 0; TRAP: False; CENTER: False;\n")

def execute_command(message, type, client_addr):
    if (type == 1):
        return MasterServer.handleRequest(message)
    elif (type == 2):
        return ScoreServer.handleRequest(message)
    elif (type == 3):
        return PlayerServer.handleRequest(message, client_addr)

# ************************* main ****************************
#sockets initiation
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# the SO_REUSEADDR flag reuses a local socket in TIME_WAIT state, without waiting for its natural timeout to expire.
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((bind_ip, bind_port))
server.listen(5)  # max backlog of connections

active_users = [] # stores all users
threads = []

# receive and handle sigint (ctrl+c)
signal.signal(signal.SIGINT, signal_handler)
generate_save()  # creates required files if no save file existant

while True:
    client_sock, address = server.accept()
    active_users.append(client_sock)
    print('Accepted connection from {}:{}'.format(address[IP], address[PORT]))
    client_handler = threading.Thread(
        target=handle_client_connection,
        # without comma you'd get a... TypeError: handle_client_connection() argument after * must be a sequence, not _socketobject
        args=(client_sock, address, )
    )
    client_handler.start()
    threads.append(client_handler)
