#!/usr/bin/env python3
import json
import socket

# Listen for connections on both localhost and internet.
HOST = ''
PORT = 8040
BATCH_SIZE = 1024


class Connection:
    """Connection - socket class superstructure

    Variables:
    socket       -- connection socket,
    host, port   -- host and port where socket connected to.

    Methods:
    str_info -- return string <host:port> whis host and port of connection.

    recv     -- recieve some json data and load it to an object.
    close    -- close socket.

    recvall  -- recieve all json data coming from other side and load it.
    sendall  -- a pair to recvall method: dump data and send it all.
    """

    def __init__(self, skt: socket.socket, host: str, port: int):
        self.socket = skt
        self.host = host
        self.port = port

    def str_info(self):
        """Return string <host:port> whis host and port of connection."""
        return self.host + ':' + str(self.port)

    def recv(self, n: int = BATCH_SIZE):
        return json.loads(self.socket.recv(n).decode())

    def close(self):
        return self.socket.close()

    def recvall(self):
        """Recieve all json data and load it.

        Get amount of data that will be transmited, then recieve it in batches.
        """
        n = int(self.socket.recv(BATCH_SIZE).decode())
        self.socket.sendall('ok'.encode())
        data = bytes()
        while len(data) < n:
            data += self.socket.recv(BATCH_SIZE)
        return json.loads(data.decode())

    def sendall(self, data):
        """Dump to json and send all data.

        Send size of the data that will be sent and send it in batches. Data
        must be json encodable.
        """
        msg = json.dumps(data).encode()
        n = len(msg)
        self.socket.sendall(str(n).encode())
        status = self.socket.recv(BATCH_SIZE).decode()
        if status == 'ok':
            left = 0
            right = BATCH_SIZE if n >= BATCH_SIZE else n
            while not n == 0:
                self.socket.sendall(msg[left:right])
                n -= right - left
                left = right
                right += BATCH_SIZE if n >= BATCH_SIZE else n


if __name__ == '__main__':
    pipe = Connection(socket.socket(), HOST, PORT)
    pipe.socket.connect((HOST, PORT))
    while True:
        com, *args = input().split()
        if com == 'close':
            pipe.sendall(dict(act='close'))
            pipe.close()
            break
        elif com == 'shutdown':
            pipe.sendall(dict(act='shutdown'))
            pipe.close()
            break
        elif com == 'echo':
            msg = dict(act='echo')
            if len(args) == 0:
                msg['msg'] = input('Enter echoing value: ')
            else:
                msg['msg'] = ''.join(args)
            pipe.sendall(msg)
        else:
            print('Unknown command {com}'.format(com))
