import socket
from threading import Thread
from socketserver import ThreadingMixIn
import os
import json
import sys


TCP_IP = 'localhost'
TCP_PORT = 9001
BUFFER_SIZE = 1024

OK = 'OK'
NOK = 'NOK'
DW = 'DOWNLOAD'
UP = 'UPLOAD'
RM = 'REMOVE'

def MENU():
    print('1.  Start Server')
    print('2.  Show Clients Connected')
    print('3.  Stop Server')

class ClientThread(Thread):
    print()

if __name__== "__main__":

    threads = []
    on_off = True

    def show_clients():
        for client in threads:
            print(client)

    def start_server(ip, port):
        tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpsock.bind((ip, port))
        while on_off:
            tcpsock.listen(5)
            print ("Waiting for incoming connections... on IP/PORT = ", TCP_IP, "/", TCP_PORT)
            (conn, (ip,port)) = tcpsock.accept()
            print('Got connection from ', ip, ', ',port)
            new_client = ClientThread(ip,port,conn)
            new_client.start()
            threads.append(new_client)
        tcpsock.close()

    def stop_server():
        on_off = False
        for client in threads:
            client.join()

    ans = input(MENU())
