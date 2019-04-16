import socket
import threading

#-- GLOBAL VARIABLES
#- SOCKETS
SERVER_PORT = 57843
BUFFER_SIZE = 1024
SERVER_IP = '127.0.0.1'

def handleRequest(msg):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP,SERVER_PORT))
    e_msg = msg.encode()
    client_socket.send(e_msg)
    full_msg = ""
    while True:
        rcv_e_msg = client_socket.recv(BUFFER_SIZE)
        rcv_msg = rcv_e_msg.decode()
        if(rcv_msg == ""):
            break
        full_msg += rcv_msg

    args = full_msg.split(":")
    print(args[2])    
    client_socket.close()

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


    

