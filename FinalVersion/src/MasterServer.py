import sys
import os
import time
import socket
import threading
import random
import fileinput
import signal
from server_module import *
from PlayerServer import *

# **************************************************************************************
#
#                             IRC PROJECT - MASTER SERVER FUNCTIONS
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
# 
# **************************************************************************************

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

def handleRequest(message, active_users):
    """
    Function that executes all actions based on command input\n
        inputs: message - command given\n
        returns: message to client
    """
    if (message[COMMAND] == PLACE and len(message) == 2):
        msg_to_client = place_item(message[COMMAND+1]) 

    # receives command and player name
    elif (message[COMMAND] == SHOW_LOC and len(message) == 2):
        # message[PLAYER_NAME] : player_name
        if (find_data(PLAY, message[PLAYERS]) != NULL):  # if player exists
            msg_to_client = show_location(message[PLAYERS])
        else:
            msg_to_client = NOK + INV_PLAYER    
    else:
        msg_to_client = NOK + INV_MSG

    return msg_to_client

def change_stats_player(player_name, pos, value):
    """
        Function that changes a certain player's stats to a received value.\n
            inputs: Player_name , attribute - name of the stat to be changed, pos - position
            of that stat in a player's line, value - new assigned value of the stat\n
            return: null
    """
    player_line = find_data(PLAY, player_name)
    line = player_line.split(";")
    temp = line[pos]
    temp += value
    line[pos] = str(temp)
    new_line = ";".join([x for x in line])
    replace_data(PLAY, player_line, new_line)

def generate_coordinates():
    # generate random coordinates
    x = random.randint(0, 4)
    y = random.randint(0, 4)
    return (x,y)

def write_map():
    rw_map.acquire_write()
    with open(filename, "w") as f:
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
        return OK + "FOOD" + PLACE_OK + " [position: " + coordinate + "]"

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

            return OK + "TRAP" + PLACE_OK + " [position: " + coordinate + "]"
        return NOK + "TRAP" + PLACE_NOK + " [there are traps everywhere]"
    else:
        # will not enter here
        return NULL

def show_location(player_name): #receives player name, finds player name, returns everything on player location.
    """
    Function that shows everything there is, in a player's location\n
        inputs: player_name\n
        returns: message to client containing all location info
    """
    return ("\n" + OK + LOCATION_OK + "\n" + "\n".join([x for x in find_data(MAP, player_name).split(";")][1:]))

def attack_player(attacker, attacked, active_users):
    """
    Function that decides the result of an attack command\n
        inputs: attacker - player1 name, attacked - player2 name\n
        returns: message to client containing the battle results
    """
    atacker = getPlayer(attacker)
    attacked = getPlayer(attacked)
    attackermsg = ''
    attackedmsg = ''

    if (atacker.GetCoords == attacked.GetCoords):
        if (attacker.GetEnrgy() == 0 or attacked.GetEnrgy() == 0):
            attackermsg = NOK + ATT_NOK + " [not enough energy to fight]"
            attackedmsg = attackermsg
        else:
            #both attacker and attacked lose one energy
            change_stats_player(attacker, ENRGY, -1)
            change_stats_player(attacked, ENRGY, -1)
            attacker.Lvlup(0,0,-1)
            attacked.Lvlup(0,0,-1)

            if ((attacker.GetAttk() + attacker.GetEnrgy() + attacker.GetExp()) /
            ((attacked.GetAttk() + attacked.GetEnrgy() + attacked.GetExp()) * random.uniform(0.5, 1.5)) > 1):
                # attacker gained experience and attacked lost one energy
                change_stats_player(attacker, EXP, 1)
                change_stats_player(attacked, ENRGY, -1)
                # attacker won and attacked lost
                change_stats_player(attacker, WON, 1)
                change_stats_player(attacked, LOST, 1)
                attacker.victory()
                attacked.defeat()
                attackermsg
                attackedmsg
            else:
                # attacked gained experience and attacker lost one energy (opposite)
                change_stats_player(attacked, EXP, 1)
                change_stats_player(attacker, ENRGY, -1)
                # attacker lost and attacked won
                change_stats_player(attacked, WON, 1)
                change_stats_player(attacker, LOST, 1)
                attacked.victory()
                attacker.defeat()
                return NOK + ATT_NOK + " [" + attacked + " won the combat and received one experience point]"
    else:

        return NOK + ATT_NOK + " [players are not in the same location]"
    
    #get attacker socket
    for i in active_users:
        if ((i.getpeername())[0] == attacker.GetAddr()):
            socket1 = i

    #get attacked socket
    for i in active_users:
        if ((i.getpeername())[0] ==  attacked.GetAddr()):
            socket2 = i

    socket1.send(attackermsg.encode())
    socket2.send(attackedmsg.encode())

def player_eat(player_name):
    """
    Function that tries to add energy to a player (eat) if location not empty (has food)\n
        inputs: player_name\n
        returns: message to client containing the output of this action
    """

    player = getPlayer(player_name)
    coordinates = player.GetCoords()
    number = table.getLoc(coordinates[0], coordinates[1])
    food = table.getFood(number)

    if (food > 0):
        if (player.GetEnrgy() < 10):
            food -= 1 
            food = table.rmFood(number)
            change_stats_player(player_name, ENRGY,1)  # increase one energy
            player.Lvlup(0,0,1)
            return OK + player_name + EAT_OK

        return NOK + player_name + EAT_NOK + " [player's energy full]"

    return NOK + player_name + EAT_NOK + " [location has no food available]"

def player_practice(player_name, option):
    """
    Function that  tries to add experience to a player (practice) if location not empty (has training center)\n
        inputs: player_name, option - either practice attack or defense\n
        returns: message to client containing the output of this action
    """
    # receives player tries to train (option: 1 - attack, 2 - defense) if location has center
    location_line = find_data(MAP, player_name)
    if (location_line.find("CENTER: True;") != -1):
        player_line = find_data(PLAY, player_name)
        line = player_line.split(";")
        energy = eval((line[ENRGY].split(":"))[VALUE_INDEX])
        if (energy > 0):
            energy -= 1
            if (option == "1"):
                # removes one energy
                change_stats_player(player_name, "ENRGY", ENRGY, -1)
                
                # increases attack
                change_stats_player(player_name, "ATT", ATTACK, 1)
                
                return OK + player_name + PRACT_OK
            elif (option == "2"):
                # removes one energy
                change_stats_player(player_name, "ENRGY", ENRGY, -1)

                # increases defense
                change_stats_player(player_name, "DEF", DEF, 1)
                
                return OK + player_name + PRACT_OK
            else:
                return NOK + INV_MSG
        else:
            NOK + player_name + PRACT_NOK + " [player has no energy left]"
    else:
        return NOK + player_name + PRACT_NOK + " [location has no training center]"

def player_trap(player_name):
    """
    Function that tries subtract energy to a player (trap) if location not empty (has trap)\n
        inputs: player_name\n
        returns: message to client containing the output of this action
    """
    # receives player , sees player position and tries to trap him if location not empty
    location_line = find_data(MAP, player_name)
    if (location_line.find("TRAP: True;") != -1):
        player_line = find_data(PLAY, player_name)
        line = player_line.split(";")
        energy = eval((line[ENRGY].split(":"))[VALUE_INDEX])
        if (energy > 0):
            # removes one energy
            change_stats_player(player_name, "ENRGY", ENRGY, -1)
            
            # increases experience
            change_stats_player(player_name, "EXP", EXP, 1)

            return OK + player_name + TRAP_OK
        else:
            return OK + player_name + TRAP_OK + " [player is dead]" # player server should remove player
    else:
        return NOK + player_name + TRAP_NOK + " [location has no trap]"

def add_player(player_name, att, defense):
    """
    Function that adds a player, if attack and defense values within accepted values\n
        inputs: player_name, att, defense \n
        returns: message to client containing the output of this action
    """
    if (player_name != NULL and (eval(att) +  eval(defense)) <= 50):
        x = random.randint(0, 4)
        y = random.randint(0, 4)
        coordinate = "(" + str(x)+", "+str(y)+")"
        

        replace_data(PLAY, NULL, player_name + " ; ATT: " + att + " ; DEF: " +
                     defense + "; EXP: 1; ENRGY: 10; COORDINATES: " + 
                     coordinate + "; WON: 0; LOST: 0;\n") # adds new player line to players.save
        
        location_line = find_data(MAP, coordinate)
        if ("PLAYERS: NULL;" in location_line):
            new_line = location_line.replace("PLAYERS: NULL;", "PLAYERS: " + player_name + ";")
        else:
            new_line = location_line.replace("PLAYERS: ", "PLAYERS: " + player_name + ", ")
        
        replace_data(MAP, location_line, new_line) # adds player_name to map.save
        return OK + ADD_OK
    else:
        return NOK + ADD_NOK

