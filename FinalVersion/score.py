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

# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
# client.connect((target, port))
client_sock.connect((TCP_IP, TCP_PORT))

#Tries to login
client_msg = IN[:-1].encode()
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
    print(args[2])    
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
    

while True:
    msg = craftCommand()
    if(msg == ""):
        continue
    else:
        handleRequest(msg)


    

