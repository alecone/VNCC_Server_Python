from cinderclient.v3 import client
from novaclient import client as novaclient
import socket
import os
from time import sleep
import subprocess as sp

mypass = 'alecone'

TCP_IP = '172.20.10.13'
BUFFER_SIZE = 1024
CREATE_VOLUME = 'VOLUME_CREATE'
DELETE_VOLUME = 'VOLUME_DELETE'
SERVER_ID = ""
OK = 'OK'
NOK = 'NOK'

volumes = {}

# Grant access to cinder API with OS_VARS
cinder = client.Client('admin', 'alecone', 'admin',
                       'http://controller:35357/v3')
nova = novaclient.Client(2, 'admin', 'alecone', 'admin',
                         auth_url='http://controller:35357/v3')
INSTANCE_ID = ''


# In order to see all methods availeble open a shell import client class
# then type help(client.volumes)

class Cindarello():

    ''' This will be the client side that will run on the controller node
        il will be in charged to execute the server side command to manage
        volumes using the openstack api cinderclient.
        The chose to run the server on the instance and the client on the 
        controller is because the instance has un ip address on the 
        apple_provider flat network which is bridged directly on the physical
        network and since the controller is not exposed it would be an issue to 
        reach it. 
    '''

    def __init__(self, sock):
        self.sock = sock
        self.sock.connect((TCP_IP, 9001))
        self.cinder = client.Client(
            'admin', 'alecone', 'admin', 'http://controller:35357/v3')
        print('Cinderello UP')

    def sudo(self, command):
        ''' sudo command executer '''

        proc = sp.Popen(['sudo', '-kS'] + command, stdin=sp.PIPE,
                        stdout=sp.PIPE, stderr=sp.PIPE)
        proc.stdin.write(mypass + '\n')
        o, e = proc.communicate()
        print(o)
        print(e)

    def create_volume(self):
        ''' Main volume creator and attachator '''

        print('CREATE AND ATTACH VOLUME COMMAND RECEIVED')
        self.sock.send(OK.encode())
        # Wait for name to give
        name = self.sock.recv(BUFFER_SIZE)
        name = name.decode('utf-8')
        print('Volume name is ', name)

        # send ok to server
        self.sock.send(OK.encode())
        disk = self.sock.recv(BUFFER_SIZE)
        disk = disk.decode('utf-8')

        # Creating a VolumeManager object -> volume
        current_volume = self.cinder.volumes.create(
            size=1, name=name, availability_zone='nova')

        print(current_volume.name)

        # per vedere se tutto va bene salva in una var res = ...
        # poi fai il check on res[0].status_code == 202

        res = self.cinder.volumes.reserve(current_volume)
        if res[0].status_code == 202:

            ''' The connector parameter is very important 
                I took this reference in order to know how the cinder api actually
                translate the REST call cinder attach, which is not that easy.
                I faces a lot of problem searching which are the parameter of the connection dict
                Finally I got that it has to be with ip, initiator and host
                Now the problem was to find the initiator, seemed to be impossible..but then
                surfing within the openstack source code with command grep -r initiator .
                i found a file in /openstack/os_brick/initiator/connector.py that list the initiator entry
                for every driver supporte. As my case is iSCSI i chose my and magically worked
            '''

            connector = {
                'ip': '10.0.0.31',
                'initiator': 'os_brick.initiator.connectors.iscsi.ISCSIConnector',
                'host': 'aleCompute1'
            }

            driver = self.cinder.volumes.initialize_connection(
                current_volume, connector)
            print(driver)
            self.cinder.volumes.attach(current_volume, INSTANCE_ID, disk)

            # # Call openstack commands
            # proc = sp.Popen(['openstack', 'server', 'add', 'volume', 'UniPgDrive', current_volume.name])
            # proc.wait()

            # Add volume to dict like user_name: volume_obj

            # Return OK
            self.sock.send(OK.encode())
        else:
            self.sock.send(NOK.encode())

    def delete_volume(self):
        ''' Main volume detachtor and distroier '''

        # res = self.cinder.volumes.begin_detaching(volume)
        # self.cinder.volumes.terminate_connection(volume, self.connector)
        # self.cinder.volumes.detach(...)
        # self.cinder.volumes.delete(volume)

    def run(self):

        while True:
            command = self.sock.recv(BUFFER_SIZE)
            command_string = command.decode('utf-8')
            if command_string == CREATE_VOLUME:
                self.create_volume()
            elif command_string == DELETE_VOLUME:
                self.delete_volume()
            else:
                print('Unsupported request')


if __name__ == "__main__":

    sock = socket.socket()
    cinder = Cindarello(sock)
    cinder.run()
