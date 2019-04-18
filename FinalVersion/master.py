import socket
import sys
import select


# **************************************************************************************
#
#                             IRC PROJECT - GAME-MASTER CLIENT
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
# 
# **************************************************************************************

#constants definition
IN = "LOGIN:MASTER\n"
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

while True:
	print('Input message to server: ')
	ins, outs, exs = select.select(inputs,[],[])
	#select assigns to list ins who is waiting to be read
	for i in ins:
		# i == sys.stdin - someone wrote on the commandline, let's read and send it to server
		if i == sys.stdin:
				user_msg = sys.stdin.readline()
				user_msg.replace(" ", "") #removes all whitespaces (no command should have whitespaces)
				client_msg = user_msg[:-1].encode() #user_msg[:-1] removes '\n' at string's end
				client_sock.send(client_msg)

				# end of connection
				if(user_msg == OUT):
					exit()

		# i == sock - server sent a message to the socket
		elif i == client_sock:
				(server_msg, addr) = client_sock.recvfrom(BUFFER_SIZE)
				server_request = server_msg.decode()
				print("Message received from server:", server_request)
