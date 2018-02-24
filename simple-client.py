# Echo client program
import socket

HOST = '192.168.102.94'    # The remote host
PORT =10000              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall('name:Rebekka')
data = s.recv(1024)
s.close()
print 'Received', repr(data)
