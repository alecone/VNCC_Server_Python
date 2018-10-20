import socket
from threading import Thread
from socketserver import ThreadingMixIn
import os
import json
import sys
import errno

ip = '192.168.0.18'
port = 2018

class ClientThread(Thread):
    def __init__(self,ip,port,sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        print ("New ClientThread started for ",ip,":",str(port))

    def run(self):
        print('Thread succefully started. Now i will shut down')

if __name__ == '__main__':
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpsock.bind((ip, port))
    while True:
        tcpsock.listen(5)
        print ("Waiting for incoming connections... on IP/PORT = ", ip, "/", port)
        (conn, (ip_client,port_client)) = tcpsock.accept()
        print('Got connection from ', ip_client, ', ',port_client)
        new_client = ClientThread(ip_client, port_client, conn)
        new_client.start()
    print('Shutting down socket')
    tcpsock.shutdown(socket.SHUT_WR)
    print('Socket disconnection from server')
