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
    rw.acquire_read() # many threads can read, if none is writting
    try:
        with open(filename, "r") as f:
            for line in f:
                found_data = line.find(str(data))
                if (found_data != -1):
                    return line
        return NULL
    finally:
        rw.release_read()

def replace_data (filename, oldline, newline):
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

def handleRequest(message):
    """
    Function that executes all actions based on command input\n
        inputs: message - command given\n
        returns: message to client
    """
    if (message[COMMAND] == PLACE_FOOD and len(message) == 1):
        msg_to_client = place_item(FOO)  # type 1 is food

    elif (message[COMMAND] == PLACE_TRAP and len(message) == 1):
        msg_to_client = place_item(TRP)  # type 1 is trap

    elif (message[COMMAND] == PLACE_CENTER and len(message) == 1):
        # type 1 is training center
        msg_to_client = place_item(CTR)

    # receives command and player name
    elif (message[COMMAND] == SHOW_LOC and len(message) == 2):
        # message[PLAYER_NAME] : player_name
        if (find_data(PLAY, message[PLAYERS]) != NULL):  # if player exists
            msg_to_client = show_location(message[PLAYERS])
        else:
            msg_to_client = NOK + INV_PLAYER

    elif (message[COMMAND] == ATT and len(message) == 3):
        # message[PLAYERS] : attacker_name / message[PLAYERS+1] : attacked_name
        if (find_data(PLAY, message[PLAYERS]) != NULL):
            msg_to_client = attack_player(message[PLAYERS], message[PLAYERS+1])
        else:
            msg_to_client = NOK + INV_PLAYER

    elif (message[COMMAND] == EAT and len(message) == 2):  # receives command and player name
        if (find_data(PLAY, message[PLAYERS]) != NULL):
            msg_to_client = player_eat(message[PLAYERS])
        else:
            msg_to_client = NOK + INV_PLAYER

    # receives command and player name
    elif (message[COMMAND] == PRACT and len(message) == 3):
        if (find_data(PLAY, message[PLAYERS]) != NULL):
            msg_to_client = player_practice(message[PLAYERS], message[PLAYERS+1])
        else:
            msg_to_client = NOK + INV_PLAYER

    # receives command and player name
    elif (message[COMMAND] == TRP and len(message) == 2):
        if (find_data(PLAY, message[PLAYERS]) != NULL):
            msg_to_client = player_trap(message[PLAYERS])
        else:
            msg_to_client = NOK + INV_PLAYER
        
    elif (message[COMMAND] == ADD_PLAYER and len(message) == 4):
        msg_to_client = add_player(message[PLAYERS], message[PLAYERS+1], message[PLAYERS+2])
    
    else:
        msg_to_client = NOK + INV_MSG

    return msg_to_client

def change_stats_player(player_name, attribute, pos, value):
    """
        Function that changes a certain player's stats to a received value.\n
            inputs: Player_name , attribute - name of the stat to be changed, pos - position
            of that stat in a player's line, value - new assigned value of the stat\n
            return: null
    """
    player_line = find_data(PLAY, player_name)
    line = player_line.split(";")
    stat = eval((line[pos].split(":"))[VALUE_INDEX])
    stat = eval((line[pos].split(":"))[VALUE_INDEX])
    stat += value

    replace_data(PLAY, player_line, player_line.replace(
        line[pos], (" " + attribute + ": " + str(stat))))

#************** commands handling functions **********************
def place_item(item_type):
    """
    Function that places a given item in a random map position\n
        inputs: item_type - FOOD, TRAP our CENTER\n
        returns: message to client
    """
    # generate random coordinates
    x = random.randint(0, 4)
    y = random.randint(0, 4)
    coordinate = "(" + str(x)+", "+str(y)+")"
    location_line = find_data(MAP, coordinate)

    if (item_type == FOO):
        if ("FOOD:" in location_line):
            line = location_line.split(";") 
            # obtains food quantity (splits "FOOD: x" , and x is in index 1)
            food = eval((line[FOOD].split(":"))[VALUE_INDEX])
            food += 1 # increases food quantity by 1
            replace_data(MAP, location_line,
                         location_line.replace(line[FOOD], (" FOOD: " + str(food))))

            return OK + FOO + PLACE_OK
        return NOK + FOO + PLACE_NOK

    elif (item_type == TRP):
        if ("TRAP: False" in location_line):
            replace_data(MAP, location_line, location_line.replace(
                "TRAP: False", "TRAP: True"))
            return OK + TRP + PLACE_OK
        return NOK + TRP + PLACE_NOK + " [location already has trap]"

    elif (item_type == CTR):
        if ("CENTER: False" in location_line):
            replace_data(MAP, location_line, location_line.replace(
                "CENTER: False", "CENTER: True"))
            return OK + CTR + PLACE_OK
        return NOK + CTR + PLACE_NOK + " [location already has training center]"
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

def attack_player(attacker, attacked):
    """
    Function that decides the result of an attack command\n
        inputs: attacker - player1 name, attacked - player2 name\n
        returns: message to client containing the battle results
    """
    location_line = find_data(MAP, attacker) # gets location line, in which attacker and attacked are
    if (attacked in location_line):
        attacker_line = find_data(PLAY, attacker)
        attacked_line = find_data(PLAY, attacked)
        
        line = attacker_line.split(";")
        attacker_stats = {
            "attack" : eval((line[ATTACK].split(":"))[VALUE_INDEX]),
            "energy" : eval((line[ENRGY].split(":"))[VALUE_INDEX]),
            "experience" : eval((line[EXP].split(":"))[VALUE_INDEX])
        }

        line2 = attacked_line.split(";")
        attacked_stats = {
            "defense" : eval((line2[ATTACK].split(":"))[VALUE_INDEX]),
            "energy" : eval((line2[ENRGY].split(":"))[VALUE_INDEX]),
            "experience" : eval((line2[EXP].split(":"))[VALUE_INDEX])
        }

        if (attacked_stats["energy"] == 0 or attacker_stats["energy"] == 0):
            return NOK + ATT_NOK + " [not enough energy to fight]"

        #both attacker and attacked lose one energy
        change_stats_player(attacker, "ENRGY", ENRGY, -1)
        change_stats_player(attacked, "ENRGY", ENRGY, -1)


        if ((attacker_stats["attack"] + attacker_stats["energy"] + attacker_stats["experience"]) /
        ((attacked_stats["defense"] + attacked_stats["energy"] + attacked_stats["experience"]) * random.uniform(0.5, 1.5)) > 1):
            # attacker gained experience and attacked lost one energy
            change_stats_player(attacker, "EXP", EXP, 1)
            change_stats_player(attacked, "ENRGY", ENRGY, -1)
            # attacker won and attacked lost
            change_stats_player(attacker, "WON", WON, 1)
            change_stats_player(attacked, "LOST", LOST, 1)
            return OK + ATT_OK + " [" + attacker + " won the combat and received one experience point]"
        else:
            # attacked gained experience and attacker lost one energy (opposite)
            change_stats_player(attacked, "EXP", EXP, 1)
            change_stats_player(attacker, "ENRGY", ENRGY, -1)
            # attacker lost and attacked won
            change_stats_player(attacked, "WON", WON, 1)
            change_stats_player(attacker, "LOST", LOST, 1)
            return NOK + ATT_NOK + " [" + attacked + " won the combat and received one experience point]"
    else:
        return NOK + ATT_NOK + " [players are not in the same location]"

def player_eat(player_name):
    """
    Function that tries to add energy to a player (eat) if location not empty (has food)\n
        inputs: player_name\n
        returns: message to client containing the output of this action
    """
    # receives player , sees player position and tries to eat if location not empty
    player_line = find_data(PLAY, player_name)
    
    # splits "COORDINATES: (x,y)" and (x,y) is at index 1
    coordinates = eval(((player_line.split(";"))[COORDINATES].split(":"))[VALUE_INDEX])

    location_line = find_data(MAP, coordinates)
    
    line = location_line.split(";")
    food = eval((line[FOOD].split(":"))[VALUE_INDEX])
    # splits "FOOD: x" , and x is at index 1

    if (food > 0):
        if ("ENRGY: 10" not in player_line):
            food -= 1
            replace_data(MAP, location_line,location_line.replace(line[FOOD], (" FOOD: " + str(food))))
 
            change_stats_player(player_name, "ENRGY", ENRGY,1)  # increase one energy
        
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

