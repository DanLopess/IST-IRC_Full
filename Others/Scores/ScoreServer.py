#------------------------------------------------------------------------------------------------------------------------------------------------------#
#---    ScoreServer.py
#---    Author: Duarte Matias
#---    Last Chnage: 08/04/2019 21:10
#------------------------------------------------------------------------------------------------------------------------------------------------------#

import threading
import socket
import signal


#-- FUNCTIONS
#- Handles interruptions to close the socket
def sigHandler(signum, frame):
    servSock.close()

#- Returns players' stats
def getStats(arg):
    unparsed_stats = []
    with open(PLAYERS, 'r') as f:
        unparsed_stats = f.readlines()
    if unparsed_stats == []:
        return ("NOK", "No players to show\n")

    unparsed_stats = list(map(lambda x: x.split("#"), filter(lambda x: '!--' not in x, unparsed_stats)))

    parsed_stats = []
    if int(arg[1]) == 6:
        for i in range(len(unparsed_stats)):
            parsed_stats += [[unparsed_stats[i][0] , int(unparsed_stats[i][1]) + int(unparsed_stats[i][2]) + int(unparsed_stats[i][3]) + int(unparsed_stats[i][4])]]
            
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
    with open(LOGS, 'r') as log:
        unparsed_log = log.readlines()
    if unparsed_log == []:
        return ("NOK", "Nothing happened yet\n")
        
    parsed_log = list(map(lambda x: x.split("#"), filter(lambda x: "!--" not in x, unparsed_log)))
    if len(arg) == 2:
        parsed_log = list(filter(lambda x: x[0] == str(arg[1]), parsed_log))
        if parsed_log == []:
            return ("NOK", "No such player " + str(arg[1]))

    res = []
    for i in parsed_log:
        res += [i[0] + " > Distance Travelled - " + i[1] + " > Food Eaten - " + i[2] + " > Times Trapped - " + i[3] + " > Times Trained - " + i[4]]
    return ("OK", "\n".join(res))

#- Returns the combat scores
def getCombatScore(arg):
    with open(COMBAT, 'r') as cmbt:
        unparsed_cmbt = cmbt.readlines()
    parsed_cmbt = list(map(lambda x: x.split("#"), filter(lambda x: "!--" not in x, unparsed_cmbt)))
    pl_info = list(filter(lambda x: arg[1] == x[0], parsed_cmbt))
    if pl_info == []:
        return ("NOK", "No such player - " + arg[1] + "\n")
    if int(pl_info[0][1]) == 0 and int(pl_info[0][2]) == 0:
        return ("NOK", "Nothing happened yet\n")
    return ("OK", pl_info[0][0] + " > Won - " + pl_info[0][1] + " > Lost - " + pl_info[0][2] + "\n")
    
#- Returns the map
def getMap(arg):
    result = []
    with open(MAP, 'r') as mp:
        positions = mp.readlines()
        positions = list(map(lambda x: str(x).split("-"), positions))
        for i in positions:
            content = i[1].split(";")
            result += [" - ".join([i[0], content[int(arg[1])-1]])]
        return ("OK", "\n".join(result))

#- Formats the answer
def craftAnswer(ans, argCode):
        return ":".join([ans[0], ANSWER_CODES[argCode], ans[1]])

#- Handles every request
def handleRequest(client):
    e_msg = client.recv(BUFFER)
    msg = e_msg.decode()
    args = msg.split(":")
    result = craftAnswer(HANDLER_FUNC[args[0]](args), args[0])
    e_res = result.encode()
    client.send(e_res)
    client.close()


#-- GLOBAL VARIABLES
#- SOCKETS
BUFFER = 1024
PORT = 57843

#- FILES
LOGS = "logs1.info"
MAP = "map.save"
PLAYERS = "stats1.info"
COMBAT = "cmbt1.info"

#- MESSAGE CODES
ANSWER_CODES = {
    'GET_STATS': "1",
    'GET_LOG': "2",
    'GET_COMBAT_SCORE': "3",
    'GET_MAP': "4"
}

#- HANDLER FUNCTION DICTIONARY
HANDLER_FUNC = {
    'GET_STATS' : getStats,
    'GET_LOG' : getLog,
    'GET_COMBAT_SCORE' : getCombatScore,
    'GET_MAP' : getMap
}


signal.signal(signal.SIGINT, sigHandler)
servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servSock.bind(('', PORT))
servSock.listen(5)

while True:
    (client, addr) = servSock.accept()
    th = threading.Thread(target=handleRequest, args= (client,), )
    th.start()

