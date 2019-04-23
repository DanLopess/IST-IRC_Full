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
#                             IRC PROJECT - MASTER & PLAYER FUNCTIONS
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
# 
# **************************************************************************************


#class containing the data relative to each payer------------------------------------------------------------------------------------------
class Player:

    def __init__(self, username, addr):
        self._username = username
        self._addr = addr
        self._Xcoord = random.randint(0,4)
        self._Ycoord = random.randint(0,4)
        self._attack = 0
        self._defense = 0
        self._experience = 0
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

        table.rmPlayer(self._username, table.getLoc(self._Xcoord,self._Ycoord))
        self._Ycoord += dir[1]
        self._Xcoord += dir[0]
        self._distance += 1
        player_move(self)
        table.addPlayer(self._username, table.getLoc(self._Xcoord,self._Ycoord))
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
        return attack_player(self._username, target._username)

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
        if (self._experience < 10):
            self._experience += quantity

    def Get_stats_terminal(self):
        return "{}:\nATTACK = {}\nDEFENSE = {}\n ENERGY = {}\n EXPERIENCE = {}\n".format(self._name, self._attack, 
            self._defense, self._energy, self._experience)

    def Get_stats_file(self):
        return ("{};{};{};{};{};{};{};{};{};{};\n"
        .format(self._username, self._attack, self._defense, self._experience, self._energy,
        self._wins, self._losses, self._distance, self._trapped, self._eaten))

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
    def getX(self):
        return self._Xcoord
    def getY(self):
        return self._Ycoord
#--------------------------------------------------------------------------------------------------------------------------------------
class Tile:
    def __init__(self, x, y, trap, food, tc, players):
        self._x = x
        self._y = y
        self._trap = trap
        self._food = food
        self._tCenter = tc
        self._players = players #key = player's name; value = player object reference

    def addPlayer(self,playerName):
        if ("NULL" in self._players):
            self._players = []
            self._players.append(playerName)
        else:
            self._players.append(playerName)


    def rmPlayer(self, playerName):
        self._players.remove(playerName)

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
                    center = False                 
                    aux = line.split(";")
                    coords = list(aux[0])
                    players = []

                    iterCount = 1
                    for i in aux[1:]:
                        
                        if iterCount == PLAYERS:
                            k = i.split(',')
                            for j in k:
                                players.append(j)
                        elif (iterCount == FOOD):
                            food = int(i)
                                
                        elif iterCount == TRAPS:
                            trap = (i == "True")
                            if trap:
                                self._traps +=1
                        
                        elif iterCount == CENTERS:
                             center = (i == "True")
                             if center:
                                 self._tc += 1
                        iterCount += 1
                        
                    self._grid += [Tile(int(coords[1]), int(coords[3]), trap, food, center, players)]

    def isTrap(self, number):
        return self._grid[number].hasTrap()

    def addPlayer(self, playerName, number):
        self._grid[number].addPlayer(playerName)

    def rmPlayer(self, playerName, number):
        self._grid[number].rmPlayer(playerName)

    def isTC(self, number):
        return self._grid[number].hasTC()

    def getLoc(self, x, y):
        return x*COLUMNS + y 

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
        table.addPlayer(name, table.getLoc(newPlayer.getX(), newPlayer.getY()))

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

def handleRequest_P(msg_request, client_addr):
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
        if len(msg_request) == 1:
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

        elif len(msg_request) == 2:
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

#TODO
# def playerExists(playerName):
#     return table.playerExist(playerName)

# def playerLogged(playerName):
#     return (playerName in active_users_ply) and active_users_ply[playerName] in player_characters

def generate_save():
    # creates game map
    if os.path.exists(MAP):
        if(os.path.getsize(MAP) == 0):
            with open(MAP, "w") as fn:
                for i in range(0, 5):
                    for f in range(0, 5):
                        fn.write("("+str(i)+","+str(f)+")"+";NULL;0;False;False;\n")

generate_save()  # creates required files if no save file existant
table = Game_map("saves/map.save")
active_users_ply = {} #dict: key: user_name; val:user_address info: example:'maria'= ('127.0.0.1',17234)
player_characters = {} #dict: key: addr; val: character object reference
player_timer = {}
first = False


# ******************** generic functions ********************
def find_data (filename, data):
    """
    This function searches for the correspondent line of either a specific coordinate or player (data) \n
        inputs: filename, data - can be either player_name or coordinates, filename - is either map or players\n
        returns: string
    """
    rw_map.acquire_read() # many threads can read, if none is writting
    try:
        with open(filename, "r") as f:
            for line in f:
                found_data = line.find(str(data))
                if (found_data != -1):
                    return line
        return NULL
    finally:
        rw_map.release_read()

def replace_data (filename, oldline, newline):
    """
    This function replaces an old line of a specific file with a new one \n
        inputs: filename, oldline - contais the line to be replaced, newline - replacing line\n
        returns: none
    """
    rw_map.acquire_write()  # only one thread a time can write to file
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
        rw_map.release_write()

def handleRequest_M(message, active_users):
    """
    Function that executes all actions based on command input\n
        inputs: message - command given\n
        returns: message to client
    """
    if (message[COMMAND] == PLACE and len(message) == 2):
        msg_to_client = place_item(message[COMMAND+1])    
    else:
        msg_to_client = NOK + INV_MSG

    return msg_to_client

def change_stats_player(player_name, pos, value):
    """
        Function that changes a certain player's stats to a received value.\n
            inputs: Player_name , pos - position
            of that stat in a player's line, value - new assigned value of the stat\n
            return: null
    """
    player_line = find_data(PLAY, player_name)
    line = player_line.split(";")
    line[pos] = str(eval(line[pos]) + value)
    new_line = ";".join([x for x in line])
    replace_data(PLAY, player_line, new_line)

def generate_coordinates():
    # generate random coordinates
    x = random.randint(0, 4)
    y = random.randint(0, 4)
    return (x,y)

def write_map():
    rw_map.acquire_write()
    with open(MAP, "w") as f:
        f.write(table.display())
    rw_map.release_write()

#************** commands handling functions **********************
def place_item(item_type):
    """
    Function that places a given item in a random map position\n
        inputs: item_type - FOOD, TRAP our CENTER\n
        returns: message to client
    """
    if (item_type == FOO):
        coordinate = generate_coordinates()
        locNumber = table.getLoc(coordinate[0], coordinate[1])
        table.placeF(locNumber)
        write_map()
        return OK + "FOOD" + PLACE_OK + " [position: " + str(coordinate) + "]"

    elif (item_type == TRP):
        if (table.getTraps() <= 25):
            while(True):
                coordinate = generate_coordinates()
                locNumber = table.getLoc(coordinate[0], coordinate[1])
                if (table.isTrap(locNumber)):
                    continue
                else:
                    table.placeT(locNumber)
                    write_map()
                    break
            return OK + "TRAP" + PLACE_OK + " [position: " + str(coordinate) + "]"
        return NOK + "TRAP" + PLACE_NOK + " [there are traps everywhere]"

    elif (item_type == CTR):
        if (table.getTC() <= 25):
            while(True):
                coordinate = generate_coordinates()
                locNumber = table.getLoc(coordinate[0], coordinate[1])
                if (table.isTC(locNumber)):
                    continue
                else:
                    table.placeTC(locNumber)
                    write_map()
                    break

            return OK + "TC" + PLACE_OK + " [position: " + str(coordinate) + "]"
        return NOK + "TC" + PLACE_NOK + " [there are training centers everywhere]"
    else:
        # will not enter here
        return NULL

def attack_player(attacker, attacked):
    """
    Function that decides the result of an attack command\n
        inputs: attacker - player1 name, attacked - player2 name\n
        returns: message to client containing the battle results
    """
    attacker_p = getPlayer(attacker)
    attacked_p = getPlayer(attacked)
    attackermsg = ''
    attackedmsg = ''

    if (attacker_p.GetCoords() == attacked_p.GetCoords()):
        if (attacker_p.GetEnrgy() == 0 or attacked_p.GetEnrgy() == 0):
            attackermsg = NOK + ATT_NOK + " [not enough energy to fight]"
            attackedmsg = attackermsg
        else:
            #both attacker and attacked lose one energy
            change_stats_player(attacker, ENRGY, -1)
            change_stats_player(attacked, ENRGY, -1)
            attacker_p.Lvlup(0,0,-1)
            attacked_p.Lvlup(0,0,-1)

            if ((attacker_p.GetAttk() + attacker_p.GetEnrgy() + attacker_p.GetExp()) /
            ((attacked_p.GetAttk() + attacked_p.GetEnrgy() + attacked_p.GetExp()) * random.uniform(0.5, 1.5)) > 1):
                # attacker gained experience and attacked lost one energy
                change_stats_player(attacker, EXP, 1)
                change_stats_player(attacked, ENRGY, -1)
                # attacker won and attacked lost
                change_stats_player(attacker, WON, 1)
                change_stats_player(attacked, LOST, 1)
                attacker_p.Victory()
                attacked_p.Defeat()
                attackermsg = "You Won the combat! Congratulations, 1 exp earned!\n"
                attackedmsg = "You have been attacked and lost 2 energy points!\n"
            else:
                # attacked gained experience and attacker lost one energy (opposite)
                change_stats_player(attacked, EXP, 1)
                change_stats_player(attacker, ENRGY, -1)
                # attacker lost and attacked won
                change_stats_player(attacked, WON, 1)
                change_stats_player(attacker, LOST, 1)
                attacker_p.Victory()
                attacked_p.Defeat()
                attackedmsg = "You Won the combat! Congratulations, 1 exp earned!\n"
                attackermsg = "You have been attacked and lost 2 energy points!\n"
    else:
        attackermsg = "You are not in the same location as the other player!\n"
    
    return attackermsg

def player_eat(player):
    """
    Function that adds energy to a player \n
        inputs: player\n
        returns: none
    """
    change_stats_player(player.getUserName(), ENRGY, 1)
    change_stats_player(player.getUserName(), EATEN, 1)

def player_practice(player, option):
    """
    Function that  tries to add experience to a player (practice) if location not empty (has training center)\n
        inputs: player_name, option - either practice attack or defense\n
        returns: none
    """
    if (option == 1):
        change_stats_player(player.getUserName(), ATTACK, player.GetAttk())
        change_stats_player(player.getUserName(), TRAINED, 1)

    elif (option == 2):
        change_stats_player(player.getUserName(), DEF, player.GetDefense())
        change_stats_player(player.getUserName(), TRAINED, 1)

def player_trap(player):
    """
    Function that subtracts energy to a player (trap)\n
        inputs: player\n
        returns: none
    """
    # receives player , sees player position and tries to trap him if location not empty

    player_name = player.getUserName()
    change_stats_player(player_name, ENRGY, player.GetEnrgy())
    change_stats_player(player.getUserName(), TRAPPED, 1)
    
def add_player(player):
    """
    Function that adds a player, if attack and defense values within accepted values\n
        inputs: player \n
        returns: none
    """
    player_name = player.getUserName()
    att = player.GetAttk()
    defense = player.GetDefense()
    coords = player.GetCoords()
    if (player_name != NULL and att + defense <= 50):
        playerL = player.Get_stats_file()
        player_line = find_data(PLAY, player_name)
        replace_data(PLAY, player_line, playerL) 
        coordinate = "("+str(coords[0])+","+str(coords[1])+")"
        location_line = find_data(MAP, coordinate)
        line = location_line.split(";")
        if (line[PLAYERS] == "NULL"):
            line[PLAYERS] = player_name
            new_line = ';'.join([x for x in line])
        elif (player_name not in line[PLAYERS]):
            line[PLAYERS] += "," + player_name
            new_line = ';'.join([x for x in line])
        else:
            new_line = location_line
            #do nothing
        replace_data(MAP, location_line, new_line) 
    else:
        #do nothing
        pass

def player_move(player):
    """
    Function that moves a player\n
        inputs: player_name\n
        returns: none
    """
    player_name = player.getUserName()
    location_line = find_data(MAP, player_name)
    line = location_line.split(";")
    players = line[PLAYERS].split(",")
    coords = player.GetCoords()
    #remove from initial coordinate
    if (len(players) == 1):
        players = "NULL"
    else:
        players.remove(players)
    line[PLAYERS] = players
    replace_data(MAP, location_line, ";".join([x for x in line])) 

    #add to new coordinate
    coordinate = "("+str(coords[0])+","+str(coords[1])+")"
    location_line = find_data(MAP, coordinate)
    line = location_line.split(";")
    if (line[PLAYERS] == "NULL"):
        line[PLAYERS] = player_name
        new_line = ';'.join([x for x in line])
    elif (player_name not in line[PLAYERS]):
        line[PLAYERS] += "," + player_name
        new_line = ';'.join([x for x in line])
    else:
        new_line = location_line
        #do nothing
    replace_data(MAP, location_line, new_line) 
    change_stats_player(player_name, ENRGY, player.GetEnrgy())  # reduce one energy
    change_stats_player(player.getUserName(), WALKED, 1)