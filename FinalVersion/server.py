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

def handle_client_connection(client_socket, address):
    # TODO
    # in this function, check what type is a client from and executes the command correspondent to that client
    logged = 0  # variable to check if client has already logged in
    while True:
        msg_from_client = client_socket.recv(MSG_SIZE)
        request = msg_from_client.decode()

        print('Received {} from {} , {}'.format(
            request, address[IP], address[PORT]))

        # Splits input message by its separation punctuation (:)
        message = request.split(":")

        if (len(message) == 1 and message[COMMAND] == LOG):  # LOGIN
            if (logged == 0):
                logged = 1
                msg_to_client = OK + LOG_OK
            elif (logged == 1):
                msg_to_client = NOK + LOG_NOK
        elif (len(message) == 1 and message[COMMAND] == LOGOUT):  # LOGOUT
            break
        else:
            msg_to_client = execute_command(message, type)

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

def find_data(filename, data):
    """
    This function searches for the correspondent line of either a specific coordinate or player (data) \n
        inputs: filename, data - can be either player_name or coordinates, filename - is either map or players\n
        returns: string
    """
    rw.acquire_read()  # many threads can read, if none is writting
    try:
        with open(filename, "r") as f:
            for line in f:
                found_data = line.find(str(data))
                if (found_data != -1):
                    return line
        return NULL
    finally:
        rw.release_read()

def replace_data(filename, oldline, newline):
    """
    This function replaces an old line of a specific file with a new one \n
        inputs: filename, oldline - contais the line to be replaced, newline - replacing line\n
        returns: none
    """
    rw.acquire_write()  # only one thread a time can write to file
    try:
        if (oldline != NULL):
            with fileinput.FileInput(filename, inplace=True, backup='.bak') as file:
                for line in file:
                    print(line.replace(oldline, newline), end='')
                    # replaces data in a given file
        else:
            if filename == PLAY and not os.path.exists(PLAY):
                with open(filename, "w") as f:
                    f.write(newline)  # adds new data
            else:
                with open(filename, "a+") as f:
                    #f.write('\n')
                    f.write(newline)  # adds new data
    finally:
        rw.release_write()

def execute_command(message, type):
    pass
# ******************** master functions ********************

# ******************** player functions ********************

# ******************** score functions ********************

# ************************* main ****************************
#sockets initiation
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# the SO_REUSEADDR flag reuses a local socket in TIME_WAIT state, without waiting for its natural timeout to expire.
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((bind_ip, bind_port))
server.listen(5)  # max backlog of connections

active_users = []
masters = {}
players = {}
scores = {}
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
