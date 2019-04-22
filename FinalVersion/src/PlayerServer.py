
import socket
import random
import sys
import signal
import time
import MasterServer
from server_module import *

# **************************************************************************************
#
#                             IRC PROJECT - PLAYER SERVER FUNCTIONS
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
# 
# **************************************************************************************

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

def handleRequest(client_msg, client_addr):
    msg_request = client_msg.decode().split(':')
    request_type = msg_request[TYPE].upper().rstrip()
    
    if request_type == "CREATE":
        server_msg = register_client(msg_request, client_addr, active_users)
        table.updatePC()
        return server_msg

    player = player_characters[client_addr]
    
    if request_type == "MOVE":
        server_msg = player.Move(msg_request[TYPE + 1])
        loc = table.getLoc(player._Xcoord, player._Ycoord)
        if(table.isTrap(loc)):
            player.Trapped()
            server_msg += " ({} was caught in a trap".format(player._username)

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

    else:
        server_msg = invalid_msg(msg_request)
    
    return server_msg


#int main(int argc,char** argv) code--------------------------------------------------------------------------------------------------------------------

table = Game_map("saves/map.save")

active_users = {} #dict: key: user_name; val:user_address info: example:'maria'= ('127.0.0.1',17234)
player_characters = {} #dict: key: addr; val: character object reference
player_timer = {}

first = False


