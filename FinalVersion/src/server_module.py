import threading


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
TRP = "TRAP"
FOO = "FOOD"
CTR = "CENTER"
MSTR = "MASTER"
PLR = "PLAYER"
SCR = "SCORE"

# ***************** score specific constants *****************
LOGS = "logs1.info"
PLAYERS = "stats1.info"
COMBAT = "cmbt1.info"
#- MESSAGE CODES
ANSWER_CODES = {
    'GET_STATS': "1",
    'GET_LOG': "2",
    'GET_COMBAT_SCORE': "3",
    'GET_MAP': "4"
}

#****************** player specific constants ******************
#message info
TYPE = 1
USER_ID = 2

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

#player client----------------------------------------------------------------------------------------------------------------------------------------------------
UP = (0, 1)
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)

#MAP----------------------------------------------------------------------------------------------------------------------------------------------------
ROWS = 5
COLUMNS = 5

#***************** master specific constants ******************

#location of certain strings in save files 
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

# ********************** possible messages ************************
LOG = 'LOGIN'
PLACE = 'PLACE'
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



# global locks
rw_map = ReadWriteLock()  # lock for one writer and many readers of a file
rw_players = ReadWriteLock()  # lock for one writer and many readers of a file
rw_logs = ReadWriteLock()  # lock for one writer and many readers of a file
rw_combats = ReadWriteLock()  # lock for one writer and many readers of a file
usr_lock = threading.Lock() # lock for user actions

#--------------------------------------------------------------------------------------------------------------------------------------
class Tile:
    def __init__(self, x, y, trap, food, tc):
        self._x = x
        self._y = y
        self._trap = trap
        self._food = food
        self._tCenter = tc
        self._players = {} #key = player's name; value = player object reference

    def hasTrap(self):
        return self._trap
    
    def hasTC(self):
        return self._tCenter

    def getFood(self):
        return self._food
    
    def display(self):
        return "({},{})-FOOD:{};TRAP:{};CENTER:{};".format(self._x, self._y, self._food, self._trap, self._tCenter)
#--------------------------------------------------------------------------------------------------------------------------------------
class Game_map:
    def __init__(self, file):
        self._grid = []
        self._playerCount = 0

        with open(file) as f:
            while True:
                line = f.readline()

                if line == "":
                    break
                else:
                    c = line.split("-")
                    coords = list(c[0])
                    
                    aux = c[1].split(";")

                    for aux2 in aux:
                        aux3 = aux2.split(":")
                        
                        if aux3[0] == "PLAYERS":
                            continue
                        
                        elif aux3[0] == "FOOD":
                            food = int(aux3[1])

                        elif aux3[0] == "TRAP":
                            trap = (aux3[1] == "True")
                        
                        elif aux3[0] == "CENTER":
                             Center = (aux3[1] == "True")

                self._grid += [Tile(int(coords[1]), int(coords[3]), trap, food, Center)]

    def isTrap(self, number):
        return self._grid[number].hasTrap()

    def isTC(self, number):
        return self._grid[number].hasTC()

    def getLoc(self, x, y):
        return x + y * COLUMNS

    def updatePC(self):
        self._playerCount += 1

    def display(self):
        for i in self._grid:
            print(i.display())
    
#class containing the data relative to each payer------------------------------------------------------------------------------------------
class Player:

    def __init__(self, username, addr):
        self._username = username
        self._addr = addr
        self._Xcoord = random.randint(0,4)
        self._Ycoord = random.randint(0,4)
        self._attack = 1
        self._defense = 1
        self._experience = 1
        self._attrPoints = 50
        self._energy = 10
        

    def Move(self, direction): #(str direction)
        direction = direction.upper()

        if direction == "UP\n" and self._Ycoord < 4:
            dir = UP
        elif direction == "DOWN\n" and self._Ycoord > 0:
            dir = DOWN
        elif direction == "LEFT\n" and self._Xcoord > 0:
            dir = LEFT
        elif direction == "RIGHT\n" and self._Xcoord < 4:
            dir = RIGHT
        else:
            return "Not a valid movement option"

        self._Ycoord += dir[1]
        self._Xcoord += dir[0]

        return "character moved to ({}, {}) succesfully".format(self._Xcoord, self._Ycoord)

    def Train(self, attr):
        attr = attr.upper()
        if(self._energy > 0):
            if attr == "ATTACK\n":
                self._attack += 1
                msg = "Attack trained"
            elif attr == "DEFENSE\n":
                self._defense += 1
                msg = "Defense trained"
            self._energy -= 1
        else:
            return "Invalid attribute"
        return msg

    def Die(self):
        return #TODO

    def Trapped(self):
        self._energy -= 1
        if self._energy == 0:
            self.Die()
        self._experience -= 1

    def Eat(self):
        if(self._energy < 10):
            self._energy += 1
        return "Yummy"

    def Attack(self, target):
        target.Die()
        return "you killed {}".format(target._username)

    def Lvlup(self, attack = 0, defense = 0):
        if attack + defense <= self._attrPoints:
            self._attack += attack
            self._defense += defense
            self._attrPoints -= attack + defense
            return True
        else:
            return False

    def View_world(self):
        return #TODO

    def GetPlayerLocation(self):
        return "PLAYER AT ({}, {})".format(self._Xcoord, self._Ycoord)
    
    def GetAddr(self):
        return self._addr

#player client END------------------------------------------------------------------------------------------------------------------------------------------------
