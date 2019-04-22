import socket
import threading
import sys

# **************************************************************************************
#
#                             IRC PROJECT - SCORE CLIENT
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
#
# **************************************************************************************

#constants definition
IN = "LOGIN:SCORE\n"
OUT = "LOGOUT\n"

TCP_IP = 'localhost'
TCP_PORT = 12345
BUFFER_SIZE = 4096

STATS_TYPES = {
    1 : 'Atk',
    2 : 'Def',
    3 : 'Exp',
    4 : 'Energy',
    5 : 'Combat',
    6 : 'Won',
    7 : 'Lost',
    8 : 
}

# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
# client.connect((target, port))
client_sock.connect((TCP_IP, TCP_PORT))

#Tries to login
client_msg = IN.strip('\n').encode()
client_sock.send(client_msg)

# select either for socket or stdin inputs
inputs = [client_sock, sys.stdin]

def handleRequest(msg):
    e_msg = msg.encode()
    client_sock.send(e_msg)
    full_msg = ""
    while True:
        rcv_e_msg = client_sock.recv(BUFFER_SIZE)
        rcv_msg = rcv_e_msg.decode()
        if(rcv_msg == ""):
            break
        full_msg += rcv_msg

    args = full_msg.split(":")
    prettyPrint(args, msg)    
    client_sock.close()

def craftCommand():
    command  = {1:"GET_STATS", 2:"GET_LOG", 3:"GET_COMBAT_SCORE", 4:"GET_MAP"}
    cmd = []
    print("1 - Get Stats\n2 - Get Log\n3 - Get Combat Score\n4 - Get Map\n")
    try:
        tmp = input("")
        if tmp not in [str(x) for x in range(1, 5)]:
            print("No such Command")
            return ""
        cmd += [command[int(tmp)]]
        if(tmp == "1"):
            print("Stat Type?\n1 - Attack\n2 - Defense\n3 - Energy\n4 - Experience\n5 - Combat\n6 - All\n")
            tmp = input("")
            if tmp not in [str(x) for x in range(1,7)]:
                print("No such Command")
                return ""
            cmd += [tmp]
            print("Order?\n1 - Top\n2 - List All\n")
            tmp = input("")
            if tmp not in [str(x) for x in range(1,3)]:
                print("No such Command")
                return ""
            cmd += [tmp]
        elif(tmp == "2"):
            print("Player name? (y/n)\n")
            tmp = input("")
            if tmp == "y":
                tmp = input("Player name: ")
                cmd += [tmp]
        elif(tmp == "3"):
            print("Player name?")
            tmp = input("")
            cmd += [tmp]
        

        elif(tmp == "4"):
            print("Map Type?\n1 - Players\n2 - Food\n3 - Traps\n4 - Training Centers\n")
            tmp = input("")
            if tmp not in [str(x) for x in range(1,5)]:
                print("No such Command")
                return ""
            cmd += [tmp]
    
        return ":".join(cmd)
    except EOFError:
            print("No input given")
            return ""   


def prettyPrint(args, msg):
    msg_lst = msg.split(":")
    print('Success' if args[0] == 'OK' else 'Error')
    if (args[1] == '1'): #Stats
        if msg_lst[1] == '1':
            print('Player > Attack:')
        elif msg_lst[1] == '2':
            print('Player > Defense:')
        elif msg_lst[1] == '3':
            print('Player > Energy:')
        elif msg_lst[1] == '4':
            print('Player > Experience:')
        elif msg_lst[1] == '5':
            print('Player > Combat Score:')
        elif msg_lst[1] == '6':
            print('Player > Stats Sum:')
        
        print(args[2])
        
    elif(args[1] == '2'): #Log
        print('Log:')
        print(args[2])

    elif(args[1] == '3'): #Combat Score
        print('Combat Scores:')
        print(args[2])

    elif(args[1] == '4'): #Map
        print('Map:\n')
        mp = args[2].split("\n")
        coords = list(map(lambda x: x.split(" - "), mp))
        if(msg[2] in ('3', '4')):
            print('  1 | 2 | 3 | 4 | 5 \n--------------------\n')
            i = 0
            while True:
                if(i > 4): break
                print('1 ' + "T" if coords[i][1] == 'True' else " " + " | " "T" if coords[i + 5][1] == 'True' else " " + " | " "T" if coords[i + 10][1] == 'True' else " " + " | " "T" if coords[i + 15][1] == 'True' else " " + " | " "T" if coords[i + 20][1] == 'True' else " ")
                print('--------------------')
                i += 1
        
        else:
            i = 0
            while True:
                if(i > 4): break
                print('1 ' + coords[i][1] + ' | ' + coords[i + 5][1] + ' | ' + coords[i + 10][1] + ' | ' + coords[i + 15][1] + coords[i + 20][1] + '\n')
                i += 1
            




while True:
    msg = craftCommand()
    if(msg == ""):
        continue
    else:
        handleRequest(msg)


    

