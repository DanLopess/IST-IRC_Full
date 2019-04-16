import sys
import os
import time
import socket
import threading
import random
import fileinput
import signal
from server_module import *

# **************************************************************************************
#
#                         IRC PROJECT - GAME SERVER
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
#
#           NOTE: ALL DEFINITIONS AND MESSAGES TYPES ARE IN SERVER_MODULE (import)
#
# Project source files: TODO
# **************************************************************************************


# TODO
# create 3 functions: execute command master, score,player
# each client is stored in a given array. 
# if the message received is from one of the clients, checks if the client exists on the array
# and if so, execute command specific to the type of client


# ******************** generic functions ********************
def signal_handler(sig, frame):
    print('You pressed Ctrl+C. Leaving...')
    server.close()  # close socket
    for i in threads:  # waits for all threads to finish, avoids corruption of data
        i.join()
    sys.exit(0)  # if multiple threads, must receive command twice


def generate_save():
    # creates game map
    if not os.path.exists(MAP):
        with open(MAP, "w") as fn:
            for i in range(0, 5):
                for f in range(0, 5):
                    fn.write(
                        str((i, f))+" ; PLAYERS: NULL; FOOD: 0; TRAP: False; CENTER: False;\n")

# ************************* main ****************************
#sockets initiation
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# the SO_REUSEADDR flag reuses a local socket in TIME_WAIT state, without waiting for its natural timeout to expire.
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((bind_ip, bind_port))
server.listen(5)  # max backlog of connections

active_users = []
threads = []
# receive and handle sigint (ctrl+c)
signal.signal(signal.SIGINT, signal_handler)
rw = ReadWriteLock()  # lock for one writer and many readers of a file
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
