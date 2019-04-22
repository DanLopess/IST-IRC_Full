#Alexandre Mota 90585
import socket
import sys
import select


#sockets communication parameters
SERVER_PORT = 12101
SERVER_IP   = '127.0.0.1'
MSG_SIZE = 1024
PACKET_NUMBER = 1


client_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# o select quer ficar a espera de ler o socket e ler do stdin (consola)
inputs = [client_sock, sys.stdin]

def player_creation():
    msg = sys.stdin.readline()
    msg = "0:CREATE:" + msg
    msg = msg.encode()
    return msg



#int main()----------------------------------------------------------------------------------------------------------------------------
print('please create your character: <name>:<attack>:<defense>')
creation_msg = player_creation()
client_sock.sendto(creation_msg,(SERVER_IP,SERVER_PORT))

while True:
  try:
    ins, outs, exs = select.select(inputs,[],[])
    #select devolve para a lista ins quem esta a espera de ler

    for i in ins:

      # i == sys.stdin - alguem escreveu na consola, vamos ler e enviar
      if i == sys.stdin:
          user_msg = sys.stdin.readline()
          user_msg = "{}:".format(PACKET_NUMBER) + user_msg
          client_msg = user_msg.encode()
          client_sock.sendto(client_msg,(SERVER_IP,SERVER_PORT))
          client_sock.settimeout(1)
          PACKET_NUMBER += 1

      # i == sock - o servidor enviou uma mensagem para o socket
      elif i == client_sock:
          client_sock.settimeout(1)
          (server_msg,addr) = client_sock.recvfrom(MSG_SIZE)
          server_request = server_msg.decode()
          print("Message received from server:", server_request)
          
  except socket.timeout:
    client_msg = user_msg.encode()
    client_sock.sendto(client_msg,(SERVER_IP,SERVER_PORT))
    client_sock.settimeout(1)
