#!/usr/bin/env python3
import json, socket

HOST = '127.0.0.1'
PORT = 8040

def get_inp():
    return input('> ')

def send(s, message):
    s.sendall(json.dumps(message).encode())

def recieve(s):
    return json.loads(s.recv(1024).decode())

sock = socket.socket()
sock.connect((HOST, PORT))
print('Connected to server on {}:{}.'.format(HOST, str(PORT)))
while True:
    action, *args = get_inp().split()
    if action == 'close':
        send(sock, dict(act='close'))
        break
    elif action == 'shutdown':
        msg = dict(act='shutdown')
        if len(args) == 0:
            msg['pass'] = input('Enter passphrase: ')
        else:
            msg['pass'] = ''.join(args)
        send(sock, msg)
        ans = recieve(sock)
        if ans['status'] == 'down':
            print(ans['msg'])
            break
        else:
            print('Error: {}.'.format(ans['descr']))
    elif action == 'echo':
        msg = dict(act='echo')
        if len(args) == 0:
            msg['val'] = input('Enter echoing value: ')
        else:
            msg['val'] = ''.join(args)
        send(sock, msg)
        ans = recieve(sock)
        if ans['status'] == 'ok':
            print('Successful.')
        else:
            print('Error: {}.'.format(ans['descr']))
    else:
        print('Unknown action: {}.'.format(action))
sock.close()
print('Disconnected from {}:{}.'.format(HOST, str(PORT)))

