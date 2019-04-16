#Alexandre Mota 90585
import socket
import random
import sys
import signal
import time


#constants definition
NULL = ''
#sockets communication parameters
SERVER_PORT = 12101
MSG_SIZE = 1024

#message info
PACKET_NUMBER = 0 
TYPE = 1
USER_ID = 2

#return codes
OK          = 'OK: '
NOT_OK      = 'ERROR: '

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
#signal handler -----------------------------------------------------------------------------------------------------------------------
def quit(sig, frame):
    server_sock.close()
    sys.exit(0)

signal.signal(signal.SIGINT, quit)

def outOfTime(sig, frame):
    server_sock.close()
    sys.exit(0)

signal.signal(signal.SIGALRM, outOfTime)
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
        self._lastPacket = 0

    def isDuplicateMsg(self, packetNo):
        return self._lastPacket == packetNo

    def Move(self, direction): #(str direction)
        direction = direction.upper()
        self._lastPacket += 1

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
        self._lastPacket += 1
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
        self._lastPacket += 1
        if(self._energy < 10):
            self._energy += 1
        return "Yummy"

    def Attack(self, target):
        self._lastPacket += 1
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


#generic functions

def find_client (addr, active_users):
    for key, val in list(active_users.items()):
        if val == addr:
            return key
    return NULL

#message handling functions
def register_client(msg_request, addr, active_users):
    #msg_request[1] = name; msg_request[2] attack; msg_request[3] = defense
    name = msg_request[USER_ID]
    msg_reply = OK + REG_OK + "\n"
    
    # delete existing users
    if name in active_users:
        active_users.pop(name)
        msg_reply = OK + REG_UPDATED + "\n"
    dst_name = find_client(addr, active_users)
    
    if (dst_name != NULL):
        active_users.pop(dst_name)
        msg_reply = OK + REG_UPDATED + "\n"
    
    # register the user
    active_users[name] = addr
    newPlayer = Player(name, addr)
    player_characters[addr] = newPlayer
    newPlayer.Lvlup(int(msg_request[USER_ID + 1]), int(msg_request[USER_ID + 2]))

    msg_reply += newPlayer.GetPlayerLocation()
    server_msg = msg_reply.encode()
    return(server_msg)

def invalid_msg(msg_request):
    respond_msg = "INVALID MESSAGE\n"
    msg_reply = NOT_OK + msg_request[TYPE] + ' ' + INV_MSG + "\n"
    server_msg = msg_reply.encode()
    return server_msg

#checks if the file is a duplicate
def checkForDup(player, packetNo):
    return player.isDuplicateMsg(packetNo)

#int main(int argc,char** argv) code--------------------------------------------------------------------------------------------------------------------

table = Game_map("map.save")

active_users = {} #dict: key: user_name; val:user_address info: example:'maria'= ('127.0.0.1',17234)
player_characters = {} #dict: key: addr; val: character object reference
player_timer = {}

server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_sock.bind(('', SERVER_PORT))
first = False

while True:
    (client_msg, client_addr) = server_sock.recvfrom(MSG_SIZE)
    msg_request = client_msg.decode().split(':')
    request_type = msg_request[TYPE].upper().rstrip()


    if request_type == "CREATE":
        server_msg = register_client(msg_request, client_addr, active_users)
        server_sock.sendto(server_msg, client_addr)
        table.updatePC()
        continue

    player = player_characters[client_addr]
    if checkForDup(player, server_msg[0]):
        continue
    
    elif request_type == "KILLSERVER":
        break
    
    elif request_type == "MOVE":
        server_msg = player.Move(msg_request[TYPE + 1])
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if(table.isTrap(loc)):
            player.Trapped()
            server_msg += " ({} was caught in a trap".format(player._username)
        server_msg = server_msg.encode()

    elif request_type == "EAT":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if(table._grid[loc].getFood() > 0):
            server_msg = player.Eat()
        else:
            server_msg = NO_FOOD
        server_msg = server_msg.encode()

    elif request_type == "TRAIN":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if table.isTC(loc):
            server_msg = player.Train(msg_request[TYPE + 1])
        else:
            server_msg = "NO TRAINING CENTER AT CURRENT LOCATION"
        server_msg = server_msg.encode()
    
    elif request_type == "INFO":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        server_msg = table._grid[loc].display()
        server_msg = server_msg.encode()
    
    elif request_type == "ATTACK":
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if len(msg_request) == 2:
            server_msg = "Select your target:\n"
            check = False
            for key in active_users:
                p2 = player_characters[active_users[key]]
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
            target = active_users[target]
            if target in player_characters:
                p2 = player_characters[target]
                x = p2._Xcoord
                y = p2._Ycoord
                loc2 = table.getLoc(x, y)
                if loc2 == loc:
                    server_msg = player.Attack(p2)
            
            else:
                server_msg = INVALID_TARGET
        server_msg = server_msg.encode()

    else:
        server_msg = invalid_msg(msg_request)

    server_sock.sendto(server_msg, client_addr)
server_sock.close()
