import sys
import os
import time
import socket
import threading
import random
import fileinput
import signal
from server_module import *
import ScoreServer
import MasterServer

# **************************************************************************************
#
#                         IRC PROJECT - GAME SERVER
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
#
#           NOTE: ALL DEFINITIONS AND MESSAGES TYPES ARE IN SERVER_MODULE (import)
#
# Project source files: server.py , server_module.py , ScoreServer.py, MasterServer.py
# clients/master.py, clients/score.py, clients/player.py
# **************************************************************************************

# ************** socket communication parameters ******************
ip = '127.0.0.1'
port = 12345
MSG_SIZE = 1024

# ******************** generic functions ********************
def signal_handler(sig, frame):
    print('You pressed Ctrl+C. Leaving...')
    server.close()  # close socket
    for i in threads:  # waits for all threads to finish, avoids corruption of data
        i.join()
    sys.exit(0)  # if multiple threads, must receive command twice

def alarm_handler(sig, frame):
    MasterServer.addAllXp()

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
                msg_to_client = execute_command(message, type, address, active_users)

            client_socket.send(msg_to_client.encode())
    else:
        msg_to_client = NOK + LOG_NOK
        client_socket.send(msg_to_client.encode())

    # end of connection
    client_socket.close()
    active_users.remove(client_socket)
    threads.remove(threading.current_thread())

def execute_command(message, type, client_addr, active_users):
    if (type == 1):
        return MasterServer.handleRequest_M(message, active_users)
    elif (type == 2):
        return ScoreServer.handleRequest(message)
    elif (type == 3):
        return MasterServer.handleRequest_P(message, client_addr)

# ************************* main ****************************
#sockets initiation
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# the SO_REUSEADDR flag reuses a local socket in TIME_WAIT state, without waiting for its natural timeout to expire.
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((ip, port))
server.listen(5)  # max backlog of connections

active_users = [] # stores all users
threads = []

# receive and handle sigint (ctrl+c)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGALRM, alarm_handler)

while True:
    client_sock, address = server.accept()
    signal.alarm(30)
    active_users.append(client_sock)
    print('Accepted connection from {}:{}'.format(address[IP], address[PORT]))
    client_handler = threading.Thread(
        target=handle_client_connection,
        # without comma you'd get a... TypeError: handle_client_connection() argument after * must be a sequence, not _socketobject
        args=(client_sock, address, )
    )
    client_handler.start()
    threads.append(client_handler)
