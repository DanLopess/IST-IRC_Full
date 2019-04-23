import threading
import random

# **************************************************************************************
#
#                             IRC PROJECT - SERVER MODULE
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
#                                        
#                                       NOTE:
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
MSTR = "MASTER"
PLR = "PLAYER"
SCR = "SCORE"
# map.save :
COORDS = 0
PLAYERS = 1
FOOD = 2
TRAPS = 3
CENTERS = 4
# players.save :
ATTACK = 1
DEF = 2
EXP = 3
ENRGY = 4
WON = 5
LOST = 6
WALKED = 7
TRAPPED = 8
EATEN = 9
TRAINED = 10

#****************** player specific constants ******************
#message info
TYPE = 0
USER_ID = 1

# return codes
OK = 'OK: '
NOT_OK = 'NOK: '

#return sub-codes
REG_OK      = 'client successfully registered'
REG_UPDATED = 'client registration updated'
REG_NOT_OK  = 'client unsuccessfully registered'
INV_CLIENT  = 'client is not registered' # invalid client
INV_SESSION = 'client has no active session'  #no active session for the client"
INV_MSG     = 'invalid message type'
INV_MOVE    = 'invalid movement'
NO_FOOD     = 'no food at present location'
ALONE_MSG   = 'no enemies at current location'
INVALID_TARGET = 'no such player at present location'

#tile arguments
PLAYERS_T = 0
FOOD_T = 1
TRAP_T = 2
CENTER_T = 3

#player client
UP = (0, 1)
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)

#MAP
ROWS = 5
COLUMNS = 5


#***************** master specific constants ******************
TRP = "T"
FOO = "F"
CTR = "TC"

# possible messages 
LOG = 'LOGIN'
PLACE = 'PLACE'
LOGOUT = 'LOGOUT'  

# return codes
OK = 'OK: '
NOK = 'NOK: '

# return sub-codes
LOG_OK = ' login successful'
PLACE_OK = ' placed successfully' 

LOG_NOK = ' failed to login'
PLACE_NOK = ' could not be placed'
INV_MSG = 'Invalid message type'

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

# global locks
rw_map = ReadWriteLock()  # lock for one writer and many readers of a file
rw_players = ReadWriteLock()  # lock for one writer and many readers of a file
usr_lock = threading.Lock() # lock for user actions
