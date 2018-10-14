import socket
from threading import Thread
from socketserver import ThreadingMixIn
import os
import json
import sys
import errno


TCP_IP = 'localhost'
TCP_PORT = 9001
BUFFER_SIZE = 1024

OK = 'OK'
NOK = 'NOK'
DW = 'DOWNLOAD'
UP = 'UPLOAD'
RM = 'REMOVE'
LIN = 'LOGIN'
LINOK = 'LOGIN_OK'
LINNOK = 'LOGIN_NOK'
REG = 'REGISTER'
REGOK = 'REGISTER_OK'
REGNOK = 'REGISTER_NOK'
LOUT = 'LOGOUT'
TREE = 'GETTREEVIEW'

def MENU():
    print('1.  Start Server')
    print('2.  Show Clients Connected')
    print('3.  Stop Server')
    print('\r\nq.  Quit ')

USERS = {}

class ClientThread(Thread):

    ''' Handler when the client connection is succesfull '''
    def __init__(self,ip,port,sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        print ("New ClientThread started for ",ip,":",str(port))

    ''' Register Command Received '''
    def register_user(self):
        # Tell user OK, send me data
        self.sock.send(OK.encode())
        # Blocking method that wait for socket bytes availeble notification
        user_pass = self.sock.recv(BUFFER_SIZE)
        user_pass = user_pass.decode('utf-8')
        print('Registration REQ by: ', user_pass)
        if '|' in user_pass:
            user_name = user_pass[0:user_pass.find('|')]
            password = user_pass[user_pass.find('|')+1:]

            # Check that domain filter in Client App has worked on properly
            must_be_domain = ['studenti.unipg.it', 'unipg.it']
            reg_domain = user_name[user_name.find('@')+1:]
            ok_domain = False
            for allowed_dom in must_be_domain:
                if reg_domain == allowed_dom:
                    ok_domain = True
                    # OK, add user to local Dictionary if not already registered
            if ok_domain:
                # TODO: this disctionary could be stored into MariaDB
                for user in USERS:
                    if user == user_name:
                        print('User already registered')
                        self.sock.send(REGNOK.encode())
                        return
                USERS.update({user_name: password})
                # Creating dir for current user added
                tmp_name = user_name[0:user_name.find('.')]
                tmp_name = tmp_name[0].upper() + tmp_name[1:]
                tmp_surname = user_name[user_name.find('.')+1:]
                tmp_surname = tmp_surname[0].upper() + tmp_surname[1:]
                dir_name = tmp_name + ' ' + tmp_surname
                try:
                    os.mkdir(dir_name)
                except:
                    raise OSError("Can't create destination directory ", dir_name)
                self.sock.send(REGOK.encode())
                # End of registration, Now user can Log IN
            else:
                print('Domain not UniPG, implement it correctly in Client App')
                self.sock.send(REGNOK.encode())
        else:
            print('User and password error, missing | : ', user_pass)
            self.sock.send(REGNOK.encode())





    ''' Main run. Client Commands dispatcher '''
    def run(self):
        while True:
            command = self.sock.recv(BUFFER_SIZE)




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

    started = False
    while True:
        MENU()
        ans = input()
        if ans == '1':
            if not started:
                main_thread = Thread(target=start_server, args=(TCP_IP, TCP_PORT,))
                main_thread.start()
                # start_server(TCP_IP, TCP_PORT)
                started = True
            else:
                print('Server is already running')
        elif ans == '2':
            show_clients()
        elif ans == '3':
            if started:
                stop_server()
                main_thread.join()
                started = False
            else:
                print('Server is not running')
        elif ans == 'q':
            break
