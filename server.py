import socket
import threading
import ast


class Server:
    def __init__(self):
        self.users = {}
        self.active_users = {}
        self.active_users_lock = threading.Lock()
        self.users_lock = threading.Lock()

    @staticmethod
    def _recvall(request):
        data = b''
        while True:
            part = request.recv(4096)
            data += part
            if len(part) < 4096:
                break
        return data

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                message_type = client_socket.recv(1).decode()

                if not message_type:
                    client_socket.close()
                    with self.active_users_lock:
                        for username, info in self.active_users.items():
                            if info["address"] == client_address:
                                sock = self.active_users.pop(username)["socket"]
                                sock.close()
                                break
                    print(f"Соединение с пользователем {client_address} закрыто")
                    break

                if message_type == '0':  # Регистрация на сервере
                    _, username, password = ast.literal_eval(self._recvall(client_socket).decode())
                    print(f'Регистрация пользователя {username}')
                    if username not in self.users:
                        with self.users_lock:
                            self.users[username] = password
                        response = "Регистрация прошла успешно"
                    else:
                        response = "Пользователь с таким именем уже зарегистрирован"
                    response_type = 0

                elif message_type == '1':  # Вход на сервер
                    _, username, password = ast.literal_eval(self._recvall(client_socket).decode())
                    print(f'Вход пользователя {username}')
                    if username in self.users and self.users[username] == password:
                        with self.active_users_lock:
                            self.active_users[username] = {
                                "socket": client_socket,
                                "address": client_address
                            }
                        response = "Вход успешен"
                    else:
                        response = "Пользователь не зарегистрирован"
                    response_type = 0

                elif message_type == '2':  # Отправка сообщения всем пользователям
                    _, username, msg = ast.literal_eval(self._recvall(client_socket).decode())
                    print(f'Отправка сообщения всем от {username}')
                    if username in self.users:
                        message_ = f"Сообщение от {username}: {msg}"
                        for user in self.active_users.values():
                            if user["address"] == client_address:
                                continue
                            with self.active_users_lock:
                                user["socket"].sendall('0'.encode())
                                user["socket"].sendall(message_.encode())
                        response = "Сообщение отправлено всем пользователям"
                    else:
                        response = "Пользователь не зарегистрирован"
                    response_type = 0

                elif message_type == '3':  # Отправка сообщения определенному пользователю
                    _, username, recipient, msg = ast.literal_eval(self._recvall(client_socket).decode())
                    print(f'Отправка сообщения от {username} к {recipient}')
                    if username in self.users and recipient in self.users:
                        if recipient in self.active_users:
                            with self.active_users_lock:
                                recipient_socket = self.active_users[recipient]["socket"]
                                message_ = f"Сообщение от {username}: {msg}"
                                recipient_socket.sendall('0'.encode())
                                recipient_socket.sendall(message_.encode())
                                response = f"Сообщение отправлено пользователю {recipient}"
                        else:
                            response = f"{recipient} не онлайн"
                    else:
                        response = "Пользователь не зарегистрирован"
                    response_type = 0

                elif message_type == '4':  # Отправка файла определенному пользователю
                    _, username, recipient = ast.literal_eval(self._recvall(client_socket).decode())

                    file_size_bytes = client_socket.recv(4)
                    if not file_size_bytes:
                        break
                    file_size = int.from_bytes(file_size_bytes, "big")
                    received_bytes = 0
                    file_data = b""
                    while received_bytes < file_size:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        file_data += data
                        received_bytes += len(data)
                    if received_bytes == file_size:
                        print(f'Отправка файла от {username} к {recipient}')
                        if username in self.users and recipient in self.users:
                            if recipient in self.active_users:
                                with self.active_users_lock:
                                    recipient_socket = self.active_users[recipient]["socket"]
                                    message = f"Файл от {username}: размер {received_bytes} байт"
                                    print(f'count_bytes = {received_bytes.to_bytes(4, "big")}')
                                    recipient_socket.sendall('1'.encode() + message.encode() + b'\n' +
                                                             received_bytes.to_bytes(4, "big") + b'\n' + file_data)
                                    response = f"Файл отправлен пользователю {recipient}"
                            else:
                                response = f"{recipient} не онлайн"
                        else:
                            response = "Пользователь не зарегистрирован"
                    else:
                        print("Ошибка при получении файла")
                    response_type = 0

                else:
                    response = "Некорректный тип сообщения"
                    response_type = 0

                client_socket.sendall(str(response_type).encode())
                client_socket.sendall(response.encode())

            except Exception as e:
                print("Ошибка при обработке сообщения:", str(e))
                print(client_socket, client_address)
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
