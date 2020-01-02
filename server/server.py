#!/usr/bin/env python3
import json, socket

# Listen for connections on all available interfaces
HOST = ''
PORT = 8040

class Connection:
    def __init__(self, skt, host, port):
        self.socket = skt
        self.host = host
        self.port = port

    def str_info(self):
        return self.host + ':' + str(self.port)

    def recv(self, n):
        return self.socket.recv(n)

    def sendall(self, data):
        return self.socket.sendall(data)

    def close(self):
        return self.socket.close()


class Server:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.bind((HOST, PORT))
        self.status = 'ok'

    def message(self, msg):
        print('[{:^4}] {}'.format(self.status, msg))

    def response(self, out, mes=''):
        if self.status == 'ok':
            msg = dict(status='ok')
        elif self.status == 'warn':
            self.message(mes)
            msg = {
                'status': 'err',
                'descr': mes
            }
        elif self.status == 'down':
            self.message(mes)
            msg = {
                'status': self.status,
                'msg': mes
            }
        out.sendall(json.dumps(msg).encode())

    def handle(self, conn):
        while True:
            self.status = 'ok'
            # TODO: Add an exception for unexpected target socket close
            data = conn.recv(1024).decode()
            if not data:
                self.status = 'fail'
                self.message('Error: empty data recieved!')
                break

            data = json.loads(data)
            if data['act'] == 'close':
                self.status = 'close'
                break
            elif data['act'] == 'shutdown':
                self.status = 'warn'
                self.message('{} server shutdown attempt.'.format(conn.str_info()))
                try:
                    if data['pass'] == 'SheparD':
                        self.status = 'ok'
                        self.message('Password verified.')
                        self.status = 'down'
                        self.response(conn, 'Shutting down server.')
                        break
                    else:
                        self.response(conn, 'Wrong shutdown passphrase.')
                except KeyError:
                    self.response(conn, 'No password provided.')
            elif data['act'] == 'echo':
                self.message('Echo requested from {}:'.format(conn.str_info()))
                mes = ''
                try:
                    print(str(data['val']))
                except KeyError:
                    self.status = 'warn'
                    mes = 'Couldn\'t find value for printing.'
                except TypeError:
                    self.status = 'warn'
                    mes = 'Couldn\'t convert given value to string.'
                self.response(conn, mes)
            else:
                self.status = 'warn'
                self.response(conn, 'Unknown action \'{}\'.'.format(data['act']))

    def serve(self):
        self.socket.listen()
        self.message('Now listening.')
        while True:
            self.status = 'ok'
            c, add = self.socket.accept()
            conn = Connection(c, *add)
            self.message('{} connected.'.format(conn.str_info()))
            self.handle(conn)
            conn.close()
            self.message('{} disconnected.'.format(conn.str_info()))
            if self.status == 'down':
                break
        self.socket.close()


if __name__ == '__main__':
    server = Server()
    server.serve()

