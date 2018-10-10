import socket
from threading import Thread
from socketserver import ThreadingMixIn
import os
import json
import sys

TCP_IP = 'localhost'
TCP_PORT = 9001
BUFFER_SIZE = 1024

LOG_IN_RET = {
'OK': 1,
'NOK': 0
}
ACK_NACK = {
'OK' : 0x01,
'NOK' : 0xFE
}

keep = True
startpath = 'C:/Users/alexa/Desktop/TesinaVNCC/VNCC_Server Python'

def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir(path)]
    else:
        d['type'] = "file"
    return d


class ClientThread(Thread):
    ''' Handler when the client connection is succesfull '''
    def __init__(self,ip,port,sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        print ("New thread started for ",ip,":",str(port))

    def run(self):
        keep_2 = True
        filename='prova.txt'
        f = open(filename,'rb')
        while keep_2:
            user_pass = self.sock.recv(BUFFER_SIZE)
            recv = user_pass.decode("utf-8")
            print('Received: ', user_pass)
            if user_pass:
                if '|' in recv:
                    user_name = recv[0:recv.find('|')]
                    password = recv[recv.find('|')+1:]
                    if user_name == 'alexandru.cone@studenti.unipg.it' and password == 'Alexandru1993':
                        print('Alexandru Cone has logged in')
                        self.sock.send(bytes([LOG_IN_RET['OK']]))
                        # Mettere una pausa o una lettura che ci fa capite che il client vuole la tree view
                        recv = self.sock.recv(BUFFER_SIZE)
                        recv = recv.decode("utf-8")
                        print('Rec: ', recv)
                        if recv == 'GET':
                            # Invio della tree directory
                            to_send = json.dumps(path_to_dict(startpath))
                            self.sock.send(to_send.encode())
                        to_download = self.sock.recv(BUFFER_SIZE)
                        to_download = to_download.decode('utf-8')
                        for file in os.walk("."):
                            if to_download in file[2]:
                                download_this = file[0]+'/'+to_download
                        with open(download_this, 'rb') as download:
                            size = os.fstat(download.fileno()).st_size
                            self.sock.send(str(size).encode())
                            #RICEVO OK = 0x01
                            n_ack = self.sock.recv(BUFFER_SIZE)
                            n_ack = n_ack.decode("utf-8")
                            if n_ack == 'OK':
                                print('OK to go from client')
                            else:
                                print(n_ack)
                            read = download.read(size)
                            while read:
                                self.sock.send(read)
                                read = download.read(BUFFER_SIZE)
                            if not read:
                                print('Finished to transfer file')
                        ans = input('Now you shold wait for client request')
                        keep = False
                        keep_2 = False
                        # l = f.read(BUFFER_SIZE)
                        # while (l):
                        #     self.sock.send(l)
                        #     print('Sent ',repr(l))
                        #     l = f.read(BUFFER_SIZE)
                        # if not l:
                        #     f.close()
                        #     self.sock.close()
                        #     print('Finished to transfer File')
                        #     break
                    else:
                        self.sock.send(bytes([LOG_IN_RET['NOK']]))
                        print('User name is: ', user_name)
                        print('Password is: ', password)
            else:
                print('Some error')
            f.close()
            self.sock.close()
            print('Finished for now...')
            break
tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind((TCP_IP, TCP_PORT))
threads = []

while keep:
    tcpsock.listen(5)
    print ("Waiting for incoming connections... on IP/PORT = ", TCP_IP, "/", TCP_PORT)
    (conn, (ip,port)) = tcpsock.accept()
    print('Got connection from ', ip, ', ',port)
    newthread = ClientThread(ip,port,conn)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()
