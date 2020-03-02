#!/usr/bin/env python3
'''server.py - entry point for server app

Defined constants:
HOST, PORT   -- host and port of interface where server will be listening on,
BATCH_SIZE   -- defines, how many bytes could be transmitted at once.

Classes:
Connections  -- socket class superstructure, redefining some of socket methods,
                slightly higher-level interface to sockets.
Handler      -- class containing connections handling logic.
Server       -- class doing main app job.
'''

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


class Handler:
    """Handler - handles connection up to its closure

    Class varibles:
    bad_statuses     -- set of statuses when handler can neither send or
                        recieve data.
    status_marks     -- a dict that associates statuses and status marks.

    Instance variables:
    connection   -- connection to handle.
    status       -- handling process status.

    Methods:
    message  -- print str_info of connection, handler 'status mark'
                and a message.
    response -- send data to client in correct form.
    handle   -- handle connection. Return 'close' or 'shut' if server shutdown
                attemt successful.
    """

    bad_statuses = {'closed', 'error'}
    status_marks = {
        'ok': 'ok',
        'warning': 'warn',
        'error': 'fail',
        'closed': 'clos',
    }

    def __init__(self, sock: socket.socket, info: tuple):
        self.connection = Connection(sock, *info)
        self.status = 'ok'

    def message(self, message: str):
        print('<{:^4}> {}: {}'.format(self.status_marks[self.status],
                                      self.connection.str_info(),
                                      message))

    def response(self, **kwargs):
        """Send data to client in correct form.

        Takes two named arguments: ``data`` for response data and ``about`` for
        errors feedback.
        Adds status to message dict following a few rules:
        1. If ``status`` is 'ok', there's also a 'data' key containing message.
        2. If ``status`` is 'error' there's also a 'about' key with error
            details.
        3. If ``status`` is 'warning', response dict must have 'about' key and
            optional 'data' key.
        """
        response = dict(status=self.status)
        response.update(kwargs)
        self.connection.sendall(response)

    def handle(self):
        self.message('connected.')
        while self.status not in self.bad_statuses:
            # NOTE: this call is not exception-safe and programm will crash if
            # any error occures.
            request = self.connection.recvall()
            if type(request) is not dict:
                self.status = 'warning'
                self.message('Wrong data recieved.')
                self.response(about='Non-dict data recieved.')
                self.status = 'ok'
                continue

            # TODO: add exceptions catchers
            if request['act'] == 'close':
                self.connection.close()
                self.status = 'closed'
                self.message('disconnected.')
                return 'closed'
            elif request['act'] == 'shutdown':
                self.message('Shutdown requested: closing connection.')
                self.response(data='Shutting down.')
                self.status = 'closed'
                self.connection.close()
                self.message('disconnected.')
                return 'shut'
            elif request['act'] == 'echo':
                self.message('Client requested echo.'
                             .format(self.connection.str_info()))
                answer = ''
                try:
                    print(request['msg'])
                except KeyError:
                    self.status = 'warning'
                    answer = 'Error while echoing: cannot find print message.'
                if answer:
                    self.message(answer)
                    self.response(about=answer)
                    self.status = 'ok'
            else:
                self.status = 'warning'
                answer = '{}: couldn\'t find request name {}.'\
                    .format(request['act'])
                self.message(answer)
                self.response(about=answer)
                self.status = 'ok'


class Server:
    """Server - main app job

    Variables:
    socket   -- socket where to listen for connections.
    status   -- status of running server. Could be either 'ok', 'warn',
                'fail' or 'down'.

    Methods:
    message  -- print a message with preceding 'status mark' - a four character
                string in square parentheses.
    serve    -- start to listen for connections, accept new ones
                and handle them.
    """

    def __init__(self):
        self.socket = socket.socket()
        self.socket.bind((HOST, PORT))
        self.status = 'ok'

    def message(self, message: str):
        print('[{:^4}] Server: {}'.format(self.status, message))

    def serve(self):
        self.socket.listen()
        while not self.status == 'shut':
            self.socket.listen()
            handler = Handler(*self.socket.accept())
            result = handler.handle()
            if result == 'shut':
                self.status = 'shut'
                self.message('Shutting down.')

        self.socket.close()


if __name__ == '__main__':
    try:
        server = Server()
        server.serve()
    except KeyboardInterrupt:
        server.socket.close()
    server.socket.close()
