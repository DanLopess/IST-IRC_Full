
import socket
import random
import sys
import signal
import time
from server_module import *
from MasterServer import attack_player,player_eat,player_practice,player_trap,add_player, player_move 

# **************************************************************************************
#
#                             IRC PROJECT - PLAYER SERVER FUNCTIONS
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
# 
# **************************************************************************************

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

#class containing the data relative to each payer------------------------------------------------------------------------------------------
class Player:

    def __init__(self, username, addr):
        self._username = username
        self._addr = addr
        self._Xcoord = random.randint(0,4)
        self._Ycoord = random.randint(0,4)
        self._attack = 0
        self._defense = 0
        self._experience = 10
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

        player_move(self)

        return "you moved to ({}, {}) succesfully ".format(self._Xcoord, self._Ycoord)

    def Train(self, attr):
        attr = attr.upper()
        tc = isTC(getLoc(self._Xcoord, self._Ycoord))
        if (tc):
            if(self._energy > 0):
                if attr == "ATTACK\n":
                    self._attack += 1
                    msg = "Attack trained"
                    player_practice(self, 1)
                elif attr == "DEFENSE\n":
                    self._defense += 1
                    msg = "Defense trained"
                    player_practice(self, 2)
                else:
                    return "Invalid attribute"
                self._energy -= 1
                self._trained += 1
            else:
                return "Not enough energy"
        else:
            return "No training center here"
        return msg

    def Trapped(self):
        self._energy -= 1
        if self._energy == 0:
            return "You fell into a trap and died. \nWait 30s to play again\n"
        self._experience -= 1
        self._trapped += 1
        player_trap(self)
        return "You fell into a trap.\n"

    def Eat(self):
        if(self._energy < 10):
            food = getFood(getLoc(self._Xcoord, self._Ycoord))
            if (food):
                self._energy += 1
                self._eaten += 1
                player_eat(self)
                return "Yummy"
            else:
                return "No food here, still hungry"
        else:
            return "Energy is full"
        

    def Attack(self, target):
        return attack_player(self, target)

    def Lvlup(self, attack = 0, defense = 0, energy = 0):
        if attack + defense <= self._attrPoints:
            self._attack += attack
            self._defense += defense
            self._energy += energy
            self._attrPoints -= attack + defense
            return True
        else:
            return False

    def changeXp(self, quantity):
        self._experience += quantity

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
    def GetDefense(self):
        return self._defense
    def GetEnrgy(self):
        return self._energy
    def GetExp(self):
        return self._experience    
    def GetCoords(self):
        return (self._Xcoord,self._Ycoord)
    def getUserName(self):
        return self._username  
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
        self._players = {}

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
                    
                    iterCount = 1
                    for i in aux[1:]:
                        players = {}
                        # if iterCount == PLAYERS:
                        #     if (i != "NULL"):
                        #         k = i.split(',')
                        #         for j in k:
                        #             if playerExists(str(j)): # TODO if playerlogged != if player exits
                        #                 player[str(j)] = getPlayer(k)
                        if (iterCount == FOOD):
                            food = int(i)
                                
                        elif iterCount == TRAPS:
                            trap = (i == "True")
                            if trap:
                                self._traps +=1
                        
                        elif iterCount == CENTERS:
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

    def playerExist(playerName):
        return playerName in players

    def display(self):
        table = []
        for i in self._grid:
            table.append(i.display())
        return '\n'.join([x for x in table])

#generic functions


def getPlayer(playerName):
    return player_characters[active_users_ply[playerName]]

def addAllXp():
    for i in active_users_ply:
        player = getPlayer(i)
        player.changeXp(1)

#message handling functions
def register_client(msg_request, addr, active_users_ply):
    #msg_request[1] = name; msg_request[2] attack; msg_request[3] = defense
    name = msg_request[USER_ID]
    msg_reply = OK + REG_OK + "\n"
    
    if (int(msg_request[USER_ID + 1]) + int(msg_request[USER_ID + 2]) <= 50):
        # delete existing users
        if name in active_users_ply:
            active_users_ply.pop(name)
            msg_reply = OK + REG_UPDATED + "\n"
            dst_name = find_client(addr, active_users_ply)
        
            if (dst_name != NULL):
                active_users_ply.pop(dst_name)
                msg_reply = OK + REG_UPDATED + "\n"
        
        # register the user
        active_users_ply[name] = addr
        newPlayer = Player(name, addr)
        player_characters[addr] = newPlayer

        newPlayer.Lvlup(int(msg_request[USER_ID + 1]), int(msg_request[USER_ID + 2]))

        msg_reply += newPlayer.GetPlayerLocation()
        add_player(newPlayer)
    else:
        msg_reply = "Invalid values."
    return msg_reply

def invalid_msg(msg_request):
    respond_msg = "INVALID MESSAGE\n"
    msg_reply = NOT_OK + msg_request[TYPE] + ' ' + INV_MSG + "\n"

    return msg_reply

def handleRequest(msg_request, client_addr):
    request_type = msg_request[TYPE].upper().rstrip()
    
    if request_type == "CREATE":
        server_msg = register_client(msg_request, client_addr, active_users_ply)
        table.updatePC()
        return server_msg

    player = player_characters[client_addr]
    
    if request_type == "MOVE":
        server_msg = player.Move(msg_request[TYPE + 1])
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if(table.isTrap(loc)):
            server_msg += player.Trapped()

    elif request_type == "EAT":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if(table._grid[loc].getFood() > 0):
            server_msg = player.Eat()
        else:
            server_msg = NO_FOOD

    elif request_type == "TRAIN":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if table.isTC(loc):
            server_msg = player.Train(msg_request[TYPE + 1])
        else:
            server_msg = "NO TRAINING CENTER AT CURRENT LOCATION"
    
    elif request_type == "INFO":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        server_msg = table._grid[loc].display()
    
    elif request_type == "ATTACK":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if len(msg_request) == 2:
            server_msg = "Select your target:\n"
            check = False
            for key in active_users_ply:
                p2 = player_characters[active_users_ply[key]]
                x = p2._Xcoord
                y = p2._Ycoord
                loc2 = table.getLoc(x, y)

                if loc2 == loc:
                    server_msg += str(key) + "\n"
                    check = True

            if not check:
                server_msg = ALONE_MSG

        else:
            target = msg_request[TYPE + 1].strip()
            target = active_users_ply[target]
            if target in player_characters:
                p2 = player_characters[target]
                x = p2._Xcoord
                y = p2._Ycoord
                loc2 = table.getLoc(x, y)
                if loc2 == loc:
                    server_msg = player.Attack(p2)
            
            else:
                server_msg = INVALID_TARGET

    else:
        server_msg = invalid_msg(msg_request)
    
    return server_msg

# def playerExists(playerName):
#     return table.playerExist(playerName)

# def playerLogged(playerName):
#     return (playerName in active_users_ply) and active_users_ply[playerName] in player_characters
#int main(int argc,char** argv) code--------------------------------------------------------------------------------------------------------------------

table = Game_map("saves/map.save")
active_users_ply = {} #dict: key: user_name; val:user_address info: example:'maria'= ('127.0.0.1',17234)
player_characters = {} #dict: key: addr; val: character object reference
player_timer = {}
first = False
