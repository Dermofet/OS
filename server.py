import socket
import threading
import ast
import time

MB = 1048576


class Server:
    def __init__(self):
        self.users = {}
        self.active_users = {}
        self.active_users_lock = threading.Lock()
        self.users_lock = threading.Lock()

    @staticmethod
    def _recvall(request):
        data = bytearray()
        while True:
            part = request.recv(MB)
            data += part
            if len(part) < MB:
                break
        return data

    @staticmethod
    def _getmsg(sock):
        messages = Server._recvall(sock)
        return messages.split(b'\x00')[:-1]

    @staticmethod
    def _sendmsg(sock, message: str):
        sock.sendall(f"{message}\x00".encode())

    def register(self, *args):
        _, _, username, password = args
        username = username.decode()
        password = password.decode()

        print(f'Регистрация пользователя {username}')

        if username in self.users:
            return "Пользователь с таким именем уже зарегистрирован"

        with self.users_lock:
            self.users[username] = password

        return "Регистрация прошла успешно"

    def login(self, *args):
        client_socket, client_address, username, password = args
        username = username.decode()
        password = password.decode()

        print(f'Вход пользователя {username}')

        if client_address in self.active_users:
            return "Этот IP адрес уже использует другой пользователь"

        if username in self.active_users:
            return "Пользователь уже вошел"

        if username not in self.users:
            return "Пользователь не зарегистрирован"

        if self.users[username] != password:
            return "Неверный пароль"

        with self.active_users_lock:
            value = (client_socket, client_address, username)
            self.active_users[client_address] = value
            self.active_users[username] = value

        return "Успешный вход"

    def send_msg_to_all_user(self, *args):
        _, client_address, message = args
        username = self.active_users[client_address][2]
        message = message.decode()

        print(f'Отправка сообщения всем от {username}')

        if client_address not in self.active_users:
            return "Вы не вошли на сервер"

        for user in set(self.active_users.values()):
            if user[1] == client_address:
                continue
            with self.active_users_lock:
                user[0].sendall(f"1\f{username}\f{message}\x00".encode())

        return "Сообщение отправлено всем пользователям"

    def send_msg_to_user(self, *args):
        _, client_address, recipient, message = args
        username = self.active_users[client_address][2]
        recipient = recipient.decode()
        message = message.decode()

        print(f'Отправка сообщения от {username} к {recipient}')

        if client_address not in self.active_users:
            return "Вы не вошли на сервер"

        if recipient not in self.users:
            return f"{recipient} не зарегистрирован"

        if recipient not in self.active_users:
            return f"{recipient} не онлайн"

        with self.active_users_lock:
            recipient_socket = self.active_users[recipient][0]
            recipient_socket.sendall(f"1\f{username}\f{message}\x00".encode())

        return f"Сообщение отправлено пользователю {recipient}"

    def send_file_to_user(self, *args):
        _, client_address, recipient, file_size, file_name, file = args
        username = self.active_users[client_address][2]
        recipient = recipient.decode()
        file_size = int(file_size.decode())
        file_name = file_name.decode().replace("/", "\\").split("\\")[-1]
        received_bytes = len(file)

        if received_bytes != file_size:
            print("Ошибка при получении файла")
            return

        print(f'Отправка файла от {username} к {recipient}, размер {received_bytes} байт')

        if client_address not in self.active_users:
            return "Вы не вошли на сервер"

        if recipient not in self.users:
            return f"{recipient} не зарегистрирован"

        if recipient not in self.active_users:
            return f"{recipient} не онлайн"

        with self.active_users_lock:
            recipient_socket = self.active_users[recipient][0]
            recipient_socket.sendall(f"2\f{username}\f{file_name}\f{received_bytes}\f".encode()
                                     + file + "\x00".encode())

        return f"Файл отправлен пользователю {recipient}"

    def close_conn(self, client_socket, client_address):
        client_socket.close()

        with self.active_users_lock:
            user = self.active_users.pop(client_address)
            self.active_users.pop(user[2])
            user[0].close()

        print(f"Соединение с пользователем {client_address} закрыто")

    def handle_client(self, client_socket, client_address):
        message_handlers = {
            '0': self.register,
            '1': self.login,
            '2': self.send_msg_to_all_user,
            '3': self.send_msg_to_user,
            '4': self.send_file_to_user
        }

        while True:
            try:
                for client_msg in self._getmsg(client_socket):
                    client_msg = client_msg.split(b'\f')
                    message_type = client_msg[0].decode()

                    if not message_type:
                        self.close_conn(client_socket, client_address)
                        break

                    if handler := message_handlers[message_type]:
                        response = handler(client_socket, client_address, *client_msg[1:])
                    else:
                        response = "Некорректный тип сообщения"

                    self._sendmsg(client_socket, f"0\f{response}")

            except Exception as e:
                print("Ошибка при обработке сообщения:", e)
                break

    def start_server(self, host, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Сервер запущен на {host}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print("Установлено соединение с клиентом", client_address)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()


if __name__ == '__main__':
    server = Server()
    server.start_server('127.0.0.1', 8888)
