import socket
from socketserver import ThreadingTCPServer, BaseRequestHandler

from user import User, UserStatus
import threading
from threading import Thread

import time
from typing import Callable, Any, Self


class RequestHandler(BaseRequestHandler):
    def handle(self):
        print(f'New connection from {self.client_address}')
        client_thread = Thread(target=self.server.process_message, args=(self.request, self.client_address))
        client_thread.start()


class Server(ThreadingTCPServer):
    def __init__(self, server_address: tuple[str, int],
                 RequestHandlerClass: Callable[[Any, Any, Self], BaseRequestHandler]):
        super().__init__(server_address, RequestHandlerClass)
        self.users = {}

    def process_message(self, client_socket, client_address):
        def recvall(sock):
            BUFF_SIZE = 4096
            res = sock.recv(BUFF_SIZE)
            return res

        # request = tuple(eval(recvall(client_socket).decode()))
        # print(f'Request: {request}')
        message_type, address, username, *data = tuple(eval(recvall(client_socket).decode()))

        match message_type:
            case 0:  # (0, address, username, password)
                msg = self.register(username, data[0])
            case 1:  # (1, address, username, password), client_address
                msg = self.login(username, data[0], client_address)
            case 2:  # (2, address, sender, msg)
                msg = self.send_msg_all_users(username, data[0])
            case 3:  # (3, address, sender, recipient, msg)
                msg = self.send_msg(username, *data)
            case 4:  # (4, address, sender, recipient, file)
                msg = self.send_file(username, *data)
            case _:
                msg = b"Unknown command"

        print(f'Answer: {msg}')
        client_socket.sendall(msg)
        print("Client was disconnected\n")

    def register(self, username, password):
        if username in self.users:
            return b"This user is already registered"

        self.users[username] = User(username, password, UserStatus.INACTIVE, None)
        return b"User successfully registered"

    def login(self, username, password, address):
        if username not in self.users:
            return b"This user is not registered"

        user = self.users[username]

        if user.password != password:
            return b"Wrong password"

        if user.status == UserStatus.ACTIVE:
            return b"This user is already logged in"

        user.status = UserStatus.ACTIVE
        user.address = address
        return b"User successfully logged in"

    @staticmethod
    def _send_msg_to_active_user(sender, recipient, message, msg_type, timestamp):
        recipient.incoming_messages.append({
            "sender": recipient.username,
            "msg": message,
            "type": msg_type,
            "timestamp": timestamp
        })

        sender.outgoing_messages.append({
            "recipient": sender.name,
            "msg": message,
            "type": msg_type,
            "timestamp": timestamp
        })

        if recipient.status == UserStatus.ACTIVE:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(recipient.address)
            sock.sendall(bytes(f'{recipient.username} - {msg}'))
            sock.close()

    def send_msg_all_users(self, username, msg):
        if username not in self.users:
            return b"This user is not registered"

        sender = self.users[username]
        if sender.status == UserStatus.INACTIVE:
            return b"This user is not logged in"

        timestamp = time.time()
        for name, user in self.users.items():
            if name == username:
                continue

            self._send_msg_to_active_user(sender, user, msg, timestamp, "msg")

        return b"Sending successfully completed"

    def send_msg(self, sender_username, recipient_username, msg):
        if sender_username not in self.users:
            return b"This user is not registered"

        sender = self.users[sender_username]

        if recipient_username not in self.users:
            return b"Recipient is not registered"

        recipient = self.users[recipient_username]

        if sender.status == UserStatus.INACTIVE:
            return b"This user is not logged in"

        timestamp = time.time()
        self._send_msg_to_active_user(sender, recipient, msg, timestamp, "msg")

        return b"Sending successfully completed"

    def send_file(self, sender_username, recipient_username, file):
        if sender_username not in self.users:
            return b"This user is not registered"

        sender = self.users[sender_username]

        if recipient_username not in self.users:
            return b"Recipient is not registered"

        recipient = self.users[recipient_username]

        if sender.status == UserStatus.INACTIVE:
            return b"This user is not logged in"

        timestamp = time.time()
        self._send_msg_to_active_user(sender, recipient, file, "file", timestamp)

        return b"Sending successfully completed"


if __name__ == '__main__':
    with Server(('', 8887), RequestHandler) as server:
        server.serve_forever()
