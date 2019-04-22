import threading
import socket
import signal
from server_module import *

# **************************************************************************************
#
#                             IRC PROJECT - SCORE SERVER FUNCTIONS
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
# 
# **************************************************************************************

#-- FUNCTIONS

#- Returns players' stats
def getStats(arg):
    unparsed_stats = []
    rw_players.acquire_read() # many threads can read, if none is writting
    with open(PLAY, 'r') as f:
        unparsed_stats = f.readlines()
    rw_players.release_read()

    if unparsed_stats == []:
        return ("NOK", "No players to show\n")

    unparsed_stats = list(map(lambda x: x.split(";"), filter(lambda x: '!--' not in x, unparsed_stats)))

    parsed_stats = []
    if int(arg[1]) == 6:
        for i in range(len(unparsed_stats)):
            parsed_stats += [[unparsed_stats[i][0] , int(unparsed_stats[i][1]) + int(unparsed_stats[i][2]) + int(unparsed_stats[i][3]) + int(unparsed_stats[i][4])]]
    elif int(args[1]) == 5:
        for i in range(len(unparsed_stats)):
            parsed_stats += [[unparsed_stats[i][0], int(unparsed_stats[i][5]) - int(unparsed_stats[i][6])]]
    else:
        for i in range(len(unparsed_stats)):
            parsed_stats += [[unparsed_stats[i][0] , int(unparsed_stats[i][int(arg[1])])]]
  
    parsed_stats.sort(key=lambda x: x[1], reverse=True)
    if int(arg[1]) == 5 and parsed_stats[0][1] == 0:
        return ("NOK", "No combats have happened yet\n")
    if int(arg[2]) == 1:
        parsed_stats = parsed_stats[:10]
    return ("OK", "\n".join(map(lambda x: " > ".join([x[0], str(x[1])]), parsed_stats)))

        
#- Returns the logs
def getLog(arg):
    rw_players.acquire_read()
    with open(PLAY, 'r') as log:
        unparsed_log = log.readlines()
    rw_players.release_read()

    if unparsed_log == []:
        return ("NOK", "Nothing happened yet\n")
        
    parsed_log = list(map(lambda x: x.split(";"), filter(lambda x: "!--" not in x, unparsed_log)))
    if len(arg) == 2:
        parsed_log = list(filter(lambda x: x[0] == str(arg[1]), parsed_log))
        if parsed_log == []:
            return ("NOK", "No such player " + str(arg[1]))

    res = []
    for i in parsed_log:
        res += [i[0] + " > Distance Travelled - " + i[7] + " > Food Eaten - " + i[9] + " > Times Trapped - " + i[8] + " > Times Trained - " + i[10]]
    return ("OK", "\n".join(res))

#- Returns the combat scores
def getCombatScore(arg):
    rw_players.acquire_read()
    with open(PLAY, 'r') as cmbt:
        unparsed_cmbt = cmbt.readlines()
    rw_players.release_read()
    parsed_cmbt = list(map(lambda x: x.split(";"), filter(lambda x: "!--" not in x, unparsed_cmbt)))
    pl_info = list(filter(lambda x: arg[1] == x[0], parsed_cmbt))
    if pl_info == []:
        return ("NOK", "No such player - " + arg[1] + "\n")
    if int(pl_info[0][1]) == 0 and int(pl_info[0][2]) == 0:
        return ("NOK", "Nothing happened yet\n")
    return ("OK", pl_info[0][0] + " > Won - " + pl_info[0][5] + " > Lost - " + pl_info[0][6] + "\n")
    
#- Returns the map
def getMap(arg):
    result = []
    rw_map.acquire_read()
    with open(MAP, 'r') as mp:
        positions = mp.readlines()
    rw_map.release_read()

    positions = list(map(lambda x: str(x).split(";"), positions))
    for i in positions:
        content = i[1:]
        result += [" - ".join([i[0], content[int(arg[1])-1]])]
    return ("OK", "\n".join(result))
    
#- Formats the answer
def craftAnswer(ans, argCode):
        return ":".join([ans[0], ANSWER_CODES[argCode], ans[1]])

#- Handles every request
def handleRequest(args):
    return craftAnswer(HANDLER_FUNC[args[0]](args), args[0])

#- HANDLER FUNCTION DICTIONARY
HANDLER_FUNC = {
    'GET_STATS' : getStats,
    'GET_LOG' : getLog,
    'GET_COMBAT_SCORE' : getCombatScore,
    'GET_MAP' : getMap
}