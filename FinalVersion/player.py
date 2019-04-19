import socket
import sys
import select

# **************************************************************************************
#
#                             IRC PROJECT - PLAYER CLIENT
#    AUTHORS - ALEXANDRE MOTA 90585, DANIEL LOPES 90590, DUARTE MATIAS 90596
#
# **************************************************************************************

#constants definition
IN = "LOGIN:PLAYER\n"
OUT = "LOGOUT\n"

TCP_IP = 'localhost'
TCP_PORT = 12345
BUFFER_SIZE = 4096

# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client_sock.connect((TCP_IP, TCP_PORT))

#Tries to login
client_msg = IN[:-1].encode()
client_sock.send(client_msg)

# select either for socket or stdin inputs
inputs = [client_sock, sys.stdin]


def player_creation():
    msg = sys.stdin.readline()
    msg = "0:CREATE:" + msg
    msg = msg.encode()
    return msg


#int main()----------------------------------------------------------------------------------------------------------------------------
print('please create your character: <name>:<attack>:<defense>')
creation_msg = player_creation()
client_sock.send(creation_msg)

while True:
    ins, outs, exs = select.select(inputs,[],[])
    #select devolve para a lista ins quem esta a espera de ler

    for i in ins:

      # i == sys.stdin - alguem escreveu na consola, vamos ler e enviar
      if i == sys.stdin:
          user_msg = sys.stdin.readline()
          client_msg = user_msg.encode()
          client_sock.send(client_msg)

      # i == sock - o servidor enviou uma mensagem para o socket
      elif i == client_sock:
          server_msg = client_sock.recv(BUFFER_SIZE)
          server_request = server_msg.decode()
          print("Message received from server:", server_request)
