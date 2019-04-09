import threading

# **************************************************************************************
#
#                            IRC PROJECT - SERVER_MODULE (import)
#                               AUTHOR - DANIEL LOPES
#
# Project source files: server.py, client.py, server_modules.py, map.save, players.save
#
#                                        NOTE:
#   map structure: 
#   "(0,0) ; PLAYERS: NULL; FOOD: 0; TRAP: False; CENTER: False;\n"
#   players structure: 
#   "PLAYER_NAME ; ATT: 25 ; DEF: 25; EXP: 25; ENRGY: 10; COORDINATES: (x,y); WON: 0; LOST: 0\n"
# **************************************************************************************

# ******************* constants definition ********************
NULL = ''
COMMAND = 0
IP = 0  # for identifying the ip address in address vector
PORT = 1  # for identifying the port in address vector
PLAY = "saves/players.save"
MAP = "saves/map.save"
TRP = "TRAP"
FOO = "FOOD"
CTR = "CENTER"

#********* location of certain strings in save files **********
#ex: in map lines structure, when split, players names will be at index 1

# map.save :
PLAYERS = 1
FOOD = 2
# players.save :
ATTACK = 1
DEF = 2
EXP = 3
ENRGY = 4
COORDINATES = 5
WON = 6
LOST = 7
# when splitting "FOOD: x" (example) , x is always at same index 1
VALUE_INDEX = 1
# note: if some indexes were not defined, that means they're not used, 
# i.e., there's no need to access the string via index

# ************** socket communication parameters ******************
bind_ip = '127.0.0.1'
bind_port = 12345
MSG_SIZE = 1024

# ********************** possible messages ************************
LOG = 'LOGIN'
PLACE_FOOD = 'PLACEF'
PLACE_TRAP = 'PLACET'
PLACE_CENTER = 'PLACEC'
ADD_PLAYER = 'ADDP'
SHOW_LOC = 'SHOW_LOCATION'
ATT = 'ATTACK'
EAT = 'EAT'
PRACT = 'PRACTICE'
LOGOUT = 'LOGOUT'  

# ************************** return codes **************************
OK = 'OK: '
NOK = 'NOK: '

#************************ return sub-codes *************************
LOG_OK = ' login successful'
PLACE_OK = ' placed successfully'
LOCATION_OK = 'location has' 
ATT_OK = ' attacked successfully'
EAT_OK = ' ate successfully'
PRACT_OK = ' practiced successfully'
TRAP_OK = ' fell into trap'
ADD_OK = ' player added successfully' 

LOG_NOK = ' failed to login'
PLACE_NOK = ' could not be placed'
ATT_NOK = ' attack failed'
EAT_NOK = ' could not eat'
PRACT_NOK = ' could not practice'
TRAP_NOK = ' could not be trapped'
INV_MSG = ' invalid message type'
INV_PLAYER = ' no such player'
ADD_NOK = ' failed to add player'

# **************************** classes ******************************
class ReadWriteLock:
    """ A lock object that allows many simultaneous "read locks", but
    only one "write lock." """

    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0

    def acquire_read(self):
        """ Acquire a read lock. Blocks only if a thread has
        acquired the write lock. """
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()

    def release_read(self):
        """ Release a read lock. """
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notifyAll()
        finally:
            self._read_ready.release()

    def acquire_write(self):
        """ Acquire a write lock. Blocks until there are no
        acquired read or write locks. """
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        """ Release a write lock. """
        self._read_ready.release()

