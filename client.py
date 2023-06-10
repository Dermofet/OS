import os.path
import socket
import threading
from typing import Union

MB = 1048576


class Client:
    def __init__(self, server_address: tuple, client_address: tuple = None):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if client_address is not None:
            self.client_socket.bind(client_address)
        self.client_socket.connect(server_address)
        self.closed = False
        self.receive_thread = threading.Thread(target=self._receive_messages)
        self.receive_thread.start()
        self.download_dir = None

    @staticmethod
    def _recvall(request):
        data = bytearray()
        while True:
            part = request.recv(MB)
            data += part
            if len(part) < MB:
                break
        return data

    def _get_messages(self):
        messages = self._recvall(self.client_socket)
        return list(messages.split(b'\x00')[:-1])

    @staticmethod
    def _server_msg(message):
        message = message.decode()
        print(f"\nСервер: {message}")

    @staticmethod
    def _user_msg(username, message):
        username = username.decode()
        message = message.decode()
        print(f"\n{username}: {message}")

    def _user_file(self, username, filename, filesize, filedata):
        username = username.decode()
        filename = filename.decode()
        filesize = int(filesize.decode())
        received_bytes = len(filedata)

        print(f"\n{username}: файл {filename}, размер {filesize}")

        if received_bytes != filesize:
            print("Ошибка при получении файла")
            print(f"Скачено {received_bytes}, ожидалось {filesize}")

        with open(f'{self.download_dir}/{filename}', "wb") as file:
            file.write(filedata)
        print("Файл успешно получен")

    def _receive_messages(self):
        while not self.closed:
            responses = self._get_messages()
            for resp in responses:
                resp = resp.split(b"\f")
                message_type = resp[0].decode()

                if not resp:
                    break

                if message_type == '0':
                    self._server_msg(*resp[1:])
                elif message_type == '1':
                    self._user_msg(*resp[1:])
                elif message_type == '2':
                    self._user_file(*resp[1:])

    def _send_message(self, message: str):
        self.client_socket.sendall((message + '\x00').encode())

    def register(self, username, password):
        self._send_message(f"0\f{username}\f{password}")

    def login(self, username, password):
        self._send_message(f"1\f{username}\f{password}")

    def send_message_all_users(self, message):
        self._send_message(f"2\f{message}")

    def send_message_to_user(self, recipient, message):
        self._send_message(f"3\f{recipient}\f{message}")

    def send_file(self, recipient, file_path):
        with open(file_path, "rb") as file:
            file_data = file.read()
        file_name = file_path.split("/")[-1]

        self.client_socket.sendall(f"4\f{recipient}\f{len(file_data)}\f{file_name}\f".encode()
                                   + file_data + "\x00".encode())

    def close(self):
        self.closed = True
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.receive_thread.join()
        self.client_socket.close()
