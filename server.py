import socket
from threading import Thread
from socketserver import ThreadingMixIn
import os
import json
import sys
import errno
import configparser
from shutil import rmtree


TCP_IP = 'localhost'#'localhost' #socket.gethostname() # '192.168.0.18'
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
ND = 'NEWDIR'
DISCONNECT = 'DISCONNECT'


def MENU():
    print('1.  Start Server')
    print('2.  Show Clients Connected')
    print('3.  Stop Server')
    print('\r\nq.  Quit ')


USERS = {}


class ClientThread(Thread):

    ''' Handler when the client connection is succesfull '''

    def __init__(self, ip, port, sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        print("New ClientThread started for ", ip, ":", str(port))
        self.user_path = ""
        self.created_dir = 1

    ''' Method that return json file of tree view'''

    def path_to_dict(self, path):
        d = {'name': os.path.basename(path)}
        if os.path.isdir(path):
            d['type'] = "directory"
            d['children'] = [self.path_to_dict(os.path.join(path, x)) for x in os.listdir(path)]
        else:
            d['type'] = "file"
        return d

    ''' Register Command Received '''

    def register_user(self):
        print('REGISTER')
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
                # Saving it into .cfg file
                cfg = configparser.ConfigParser()
                cfg.read('server_config.cfg')
                cfg.set('USERS', user_name, password)
                with open('server_config.cfg', 'w') as configfile:
                    cfg.write(configfile)
                USERS.update({user_name: password})
                # Creating dir for current user added
                # TODO: Should change when will be in a cloud context
                user_name = user_name[0:user_name.find('@')]
                tmp_name = user_name[0:user_name.find('.')]
                tmp_name = tmp_name[0].upper() + tmp_name[1:]
                tmp_surname = user_name[user_name.find('.')+1:]
                tmp_surname = tmp_surname[0].upper() + tmp_surname[1:]
                dir_name = tmp_name + ' ' + tmp_surname
                try:
                    if os.name == 'nt':
                        # Windows user
                        os.makedirs(dir_name)
                    elif os.name == 'posix':
                        # Linux user
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

    ''' Login Command Received '''

    def login_user(self):
        print('LOGIN')
        # Tell user OK, send me data
        self.sock.send(OK.encode())
        # Blocking method that wait for socket bytes availeble notification
        user_pass = self.sock.recv(BUFFER_SIZE)
        user_pass = user_pass.decode('utf-8')
        print('Login REQ by: ', user_pass)
        if '|' in user_pass:
            user_name = user_pass[0:user_pass.find('|')]
            password = user_pass[user_pass.find('|')+1:]
            # TODO: this disctionary could be stored into MariaDB
            ok_to_log = False
            for user in USERS:
                if user == user_name:
                    if USERS[user] == password:
                        print('User correctly registered, allowed to LOGIN')
                        ok_to_log = True
                        break
                    else:
                        print('Wrong password')
                        break
            else:
                print('User Name not registered')
            # Saving it into .cfg file
            if ok_to_log:
                # Setting dir for current user
                user_name = user_name[0:user_name.find('@')]
                tmp_name = user_name[0:user_name.find('.')]
                tmp_name = tmp_name[0].upper() + tmp_name[1:]
                tmp_surname = user_name[user_name.find('.')+1:]
                tmp_surname = tmp_surname[0].upper() + tmp_surname[1:]
                dir_name = tmp_name + ' ' + tmp_surname
                # TODO: Should change when will be in a cloud context
                self.user_path = os.getcwd()
                if os.name == 'nt':
                    # Windows user
                    self.user_path = self.user_path.replace("\\", "/")
                    self.user_path = self.user_path + "/" + dir_name
                elif os.name == 'posix':
                    # Linux user
                    self.user_path = self.user_path + "/" + dir_name
                self.sock.send(LINOK.encode())
                # End of Log IN, Now user will ask for GETTREEVIEW
            else:
                print('Log in error for: ', user_pass)
                self.sock.send(LINNOK.encode())
        else:
            print('User and password error, missing | : ', user_pass)
            self.sock.send(REGNOK.encode())

    ''' Method that send the tree view to the client '''

    def set_tree_view(self):
        print('TREE')
        to_send = json.dumps(self.path_to_dict(self.user_path))
        self.sock.send(to_send.encode())

    ''' Method for download the file '''

    def download(self):
        print('DOWNLOAD')
        self.sock.send(OK.encode())
        to_download = self.sock.recv(BUFFER_SIZE)
        to_download = to_download.decode('utf-8')
        for file in os.walk("."):
            if to_download in file[2]:
                download_this = file[0]+'/'+to_download
        with open(download_this, 'rb') as download:
            size = os.fstat(download.fileno()).st_size
            self.sock.send(str(size).encode())
            # Waiting for ok to go
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

    ''' Method for upload the file '''

    def upload(self):
        print('UPLOAD')
        self.sock.send(OK.encode())
        upload_dest_dir = self.sock.recv(BUFFER_SIZE)
        upload_dest_dir = upload_dest_dir.decode('utf-8')
        self.sock.send(OK.encode())
        upload_file_name = self.sock.recv(BUFFER_SIZE)
        upload_file_name = upload_file_name.decode('utf-8')
        self.sock.send(OK.encode())
        length_file = self.sock.recv(BUFFER_SIZE)
        length_file = length_file.decode('utf-8')
        length_file = int(float(length_file))
        self.sock.send(OK.encode())
        # Now ready to receive file
        # Check if file already exist
        print(upload_dest_dir)
        print(self.user_path.split('/')[-1])
        if upload_dest_dir == self.user_path.split('/')[-1]:
            full_file = upload_dest_dir
        else:
            for root, dir, file in os.walk(self.user_path):
                if upload_dest_dir in dir:
                    full_file = root + '/' + upload_dest_dir
                    break
            else:
                print('Non ho trovato il cartell0')
        # full_file = os.path.abspath(upload_dest_dir)
        print(full_file)
        if os.name == 'nt':
            full_file.replace("\\", "/")
        full_file = full_file + '/' + upload_file_name
        exists = os.path.isfile(full_file)
        if exists:
            print('File already exist. It will be overwritten')
        f = open(full_file, 'wb+')
        # recv = self.sock.recv(BUFFER_SIZE)
        # f.write(recv)
        # print("Received ", len(recv))
        # left = length_file - len(recv)
        left = length_file
        # print('Left', left)
        while left > 0:
            recv = self.sock.recv(BUFFER_SIZE)
            # print("Received ", len(recv))
            f.write(recv)
            left = left - len(recv)
            # print('Left', left)
        f.close()
        print('Finished upload')
        self.sock.send(OK.encode())


    ''' Method for remove the file '''

    def remove(self):
        print('REMOVE')
        self.sock.send(OK.encode())
        to_remove = self.sock.recv(BUFFER_SIZE)
        to_remove = to_remove.decode('utf-8')
        # Check if the user want to destry it's cloud
        if to_remove == self.user_path:
            self.sock.send(NOK.encode())
            print('Action disabled for now')
            return
        if '.' in to_remove:
            # Search file and remove
            for file in os.walk(self.user_path):
                if to_remove in file[2]:
                    remove_this = file[0]+'/'+to_remove
            os.remove(remove_this)
            check_remove = os.path.isfile(remove_this)
        else:
            # Directory case
            full_file = ''
            for root, dir, file in os.walk(self.user_path):
                if to_remove in dir:
                    full_file = root + '/' + to_remove
                    break
            else:
                print('Non ho trovato il cartell0')
            rmtree(full_file)
            check_remove = os.path.isdir(full_file)
        if not check_remove:
            print('OK File eliminato')
            self.sock.send(OK.encode())
        else:
            self.sock.send(NOK.encode())

    ''' Method for create new dir '''

    def new_dir(self):
        print('NEW_DIR')
        self.sock.send(OK.encode())
        where_to_create = self.sock.recv(BUFFER_SIZE)
        where_to_create = where_to_create.decode('utf-8')
        # Search folder and create sub folder
        print(where_to_create)
        print(self.user_path.split('/')[-1])
        if where_to_create == self.user_path.split('/')[-1]:
            full_dir_path = where_to_create
        else:
            for root, dir, file in os.walk(self.user_path):
                if where_to_create in dir:
                    full_dir_path = root + '/' + where_to_create
                    break
            else:
                print('Non ho trovato il cartell0')
            print(full_dir_path)
        if os.name == 'nt':
            new_dir_path = full_dir_path + "\\" + "Folder " + str(self.created_dir)
        else:
            new_dir_path = full_dir_path + "/" + "Folder " + str(self.created_dir)
        check_created = os.path.isdir(new_dir_path)
        self.created_dir = self.created_dir + 1
        while check_created:
            if os.name == 'nt':
                new_dir_path = full_dir_path + "\\" + "Folder " + str(self.created_dir)
            else:
                new_dir_path = full_dir_path + "/" + "Folder " + str(self.created_dir)
            check_created = os.path.isdir(new_dir_path)
            self.created_dir = self.created_dir + 1
        try:
            if os.name == 'nt':
                # Windows user
                os.makedirs(new_dir_path)
            elif os.name == 'posix':
                # Linux user
                os.mkdir(new_dir_path)
        except:
            raise OSError("Can't create destination directory ", new_dir_path)
        check_created = os.path.isdir(new_dir_path)
        if check_created:
            print('OK Folder creato')
            self.sock.send(OK.encode())
        else:
            self.sock.send(NOK.encode())


    ''' Main run. Client Commands dispatcher '''

    def run(self):
        while keep_client_alive:
            command = self.sock.recv(BUFFER_SIZE)
            command_string = command.decode('utf-8')
            if command_string == REG:
                self.register_user()
            elif command_string == LIN:
                self.login_user()
            elif command_string == TREE:
                self.set_tree_view()
            elif command_string == DW:
                self.download()
            elif command_string == UP:
                self.upload()
            elif command_string == RM:
                self.remove()
            elif command_string == ND:
                self.new_dir()
            elif command_string == DISCONNECT:
                print('DISCONNECTION Req from client')
                break
        print('Client stopped')


if __name__ == "__main__":

    threads = []

    def show_clients():
        for client in threads:
            print(client)

    def start_server(ip, port):
        tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpsock.bind((ip, port))
        while True:
            tcpsock.listen(5)
            print("Waiting for incoming connections... on IP/PORT = ", ip, "/", port)
            (conn, (ip_client, port_client)) = tcpsock.accept()
            print('Got connection from ', ip_client, ', ',port_client)
            new_client = ClientThread(ip_client, port_client, conn)
            new_client.start()
            threads.append(new_client)
            if off:
                break
        print('Shutting down socket')
        tcpsock.shutdown(socket.SHUT_WR)
        print('Socket disconnection from server')

    def stop_server():
        global keep_client_alive
        global off
        print('Closing clients from server')
        keep_client_alive = False
        for client in threads:
            print('Joining thread')
            client.join()
        print('Clients closed')
        off = True

    started = False
    cfg = configparser.ConfigParser()
    cfg.read('server_config.cfg')
    for sec in cfg.sections():
        if sec == 'USERS':
            # Load USERS
            for user in cfg['USERS']:
                USERS.update({user: cfg['USERS'][user]})

    while True:
        MENU()
        ans = input()
        if ans == '1':
            if not started:
                off = False
                keep_client_alive = True
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
