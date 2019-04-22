import threading
import random
from MasterServer import attack_player
from PlayerServer import *
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
# ***************** score specific constants *****************
#- MESSAGE CODES
ANSWER_CODES = {
    'GET_STATS': "1",
    'GET_LOG': "2",
    'GET_COMBAT_SCORE': "3",
    'GET_MAP': "4"
}

#****************** player specific constants ******************
#message info
TYPE = 0
USER_ID = 1

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
PLAYERS = 0
FOOD = 1
TRAP = 2
CENTER = 3

#player client----------------------------------------------------------------------------------------------------------------------------------------------------
UP = (0, 1)
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)

#MAP----------------------------------------------------------------------------------------------------------------------------------------------------
ROWS = 5
COLUMNS = 5

#***************** master specific constants ******************
TRP = "T"
FOO = "F"
CTR = "C"

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

#--------------------------------------------------------------------------------------------------------------------------------------
class Tile:
    def __init__(self, x, y, trap, food, tc, players):
        self._x = x
        self._y = y
        self._trap = trap
        self._food = food
        self._tCenter = tc
        self._players = players #key = player's name; value = player object reference

    def placeT(self):
        self._trap = True

    def placeF(self):
        self._food += 1

    def placeTC(self):
        self._tCenter = True

    def hasTrap(self):
        return self._trap
    
    def hasTC(self):
        return self._tCenter

    def getFood(self):
        return self._food
    
    def rmFood(self):
        self._food -= 1

    def display(self):
        return "({},{});{};{};{};{};".format(self._x, self._y, ','.join([x for x in self._players]) ,self._food, self._trap, self._tCenter)
#--------------------------------------------------------------------------------------------------------------------------------------
class Game_map:
    def __init__(self, file):
        self._grid = []
        self._playerCount = 0
        self._traps = 0
        self._tc = 0

        with open(file) as f:
            while True:
                line = f.readline()

                if line == "":
                    break
                else: 
                    trap = False
                    food = 0
                    Center = False                 
                    aux = line.split(";")
                    coords = list(aux[0])

                    iterCount = 0
                    for i in aux[1:]:
                         
                        if iterCount == PLAYERS:
                            players = {}
                            k = i.split(',')
                            for j in k:
                                if playerExists(str(j)):
                                    player[str(j)] = getPlayer(k)

                        elif iterCount == FOOD:
                            food = int(i)
                                
                        elif iterCount == TRAP:
                            trap = (i == "True")
                            if trap:
                                self._traps +=1
                        
                        elif iterCount == CENTER:
                             Center = (i == "True")
                             if Center:
                                 self._tc += 1

                        iterCount += 1
                    self._grid += [Tile(int(coords[1]), int(coords[3]), trap, food, Center, players)]


    def isTrap(self, number):
        return self._grid[number].hasTrap()

    def isTC(self, number):
        return self._grid[number].hasTC()

    def getLoc(self, x, y):
        return x + y * COLUMNS

    def updatePC(self):
        self._playerCount += 1

    def placeT(self, number):
        self._grid[number].placeT()

    def placeF(self, number):
        self._grid[number].placeF()

    def placeTC(self, number):
        self._grid[number].placeTC()

    def getTraps(self):
        return self._traps

    def getTC(self):
        return self._tc

    def getFood(self, number):
        return self._grid[number].getFood()
    
    def rmFood(self, number):
        return self._grid[number].rmFood()

    def display(self):
        table = []
        for i in self._grid:
            table.append(i.display())
        return '\n'.join([x for x in table])

table = Game_map("saves/map.save")

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
        self._distance = 0
        self._trapped = 0
        self._eaten = 0
        self._trained = 0
        self._wins = 0
        self._losses = 0


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
        self._distance += 1
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

        self._trained += 1
        return msg

    def Trapped(self):
        self._energy -= 1
        if self._energy == 0:
            self.Die()
        self._experience -= 1
        self._traped += 1

    def Eat(self):
        if(self._energy < 10):
            self._energy += 1
            self._eaten += 1
            return "Yummy"
        return "No food here still hungry"

    def Attack(self, target):
        from MasterServer import attack_player
        attack_player(self, target)
        return ""

    def Lvlup(self, attack = 0, defense = 0, energy = 0):
        if attack + defense <= self._attrPoints:
            self._attack += attack
            self._defense += defense
            self._energy += energy
            self._attrPoints -= attack + defense
            return True
        else:
            return False

    def Get_stats_terminal(self):
        return "{}:\nATTACK = {}\nDEFENSE = {}\n ENERGY = {}\n EXPERIENCE = {}\n".format(self._name, self._attack, 
            self._defense, self._energy, self._experience)

    def Get_stats_file(self):
        return ("{};{};{};{};{};{}};{};{};{};{};"
        .format(self._name, self._attack, self._defense, self._experience, self._energy,
        self._wins, self._losses, self._distance, self.trapped, self._eaten))

    def GetPlayerLocation(self):
        return "PLAYER AT ({}, {})".format(self._Xcoord, self._Ycoord)
    
    def GetAddr(self):
        return self._addr

    def Victory(self):
        self._experience += 1
        self._wins += 1

    def Defeat(self):
        self._losses += 1
        self._energy -= 1

    def GetAttk(self):
        return self._attack
    def GetEnrgy(self):
        return self._energy
    def GetExp(self):
        return self._experience
    
    def GetCoords(self):
        return (self._Xcoord,self._Ycoord)

#player client END------------------------------------------------------------------------------------------------------------------------------------------------
