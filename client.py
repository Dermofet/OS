import socket
import threading


class Client:
    def __init__(self, server_address: tuple):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(server_address)
        self.closed = False
        self.receive_thread = threading.Thread(target=self._receive_messages)
        self.receive_thread.start()
        self.response_event = threading.Event()

    def _receive_messages(self):
        while not self.closed:
            response = self.client_socket.recv(1)

            if not response:
                break

            response = response.decode()

            if response == '0':
                while True:
                    response = self.client_socket.recv(4096).decode()
                    print(response)
                    if len(response) < 4096:
                        break
            elif response == '1':
                response = self.client_socket.recv(4096)
                if not response:
                    break
                response = response.split(b'\n')
                print(response[0].decode())

                file_size = int.from_bytes(response[1], "big")
                file_data = b''.join(response[2:])
                received_bytes = len(file_data)
                while received_bytes < file_size:
                    data = self.client_socket.recv(4096)
                    if not data:
                        break
                    file_data += data
                    received_bytes += len(data)
                if received_bytes == file_size:
                    with open("Bob/file.txt", "wb") as file:
                        file.write(file_data)
                    print("Файл успешно получен")
                else:
                    print(received_bytes)
                    print("Ошибка при получении файла")

            self.response_event.set()

    def _sendmsg(self, message):
        self.response_event.clear()  # Сбрасываем сигнал о получении ответа
        self.client_socket.sendall(str(message).encode())

    def _wait_for_response(self):
        self.response_event.wait()  # Ожидаем получение ответа от сервера

    def register(self, username, password):
        self._sendmsg(0)
        self._sendmsg((0, username, password))
        self._wait_for_response()

    def login(self, username, password):
        self._sendmsg(1)
        self._sendmsg((0, username, password))
        self._wait_for_response()

    def send_message_all_users(self, username, message):
        self._sendmsg(2)
        self._sendmsg((2, username, message))
        self._wait_for_response()

    def send_message(self, username, recipient, message):
        self._sendmsg(3)
        self._sendmsg((1, username, recipient, message))
        self._wait_for_response()

    def send_file(self, username, recipient, file_path):
        self._sendmsg(4)
        self._sendmsg((1, username, recipient))
        with open(file_path, "rb") as file:
            file_data = file.read()
        file_size = len(file_data).to_bytes(4, "big")
        self.client_socket.sendall(file_size)
        self.client_socket.sendall(file_data)
        self.response_event.clear()
        self.response_event.wait()

    def close(self):
        self.closed = True
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.receive_thread.join()
        self.client_socket.close()


class Menu:
    @staticmethod
    def menu(menu_text: str | list[str] | tuple[str]):
        if isinstance(menu_text, str):
            print(menu_text)
        elif isinstance(menu_text, (list, tuple)):
            for i, string in enumerate(menu_text):
                print(f'{i}. {string}')

    @staticmethod
    def input() -> int:
        # try:
        choice = int(input("Ваш выбор: "))
        return choice
        # except E


def run():
    client = Client(("127.0.0.1", 8888))
    menu_text = (
            "Выход",
            "Регистрация",
            "Вход",
            "Отправить сообщение всем пользователям",
            "Отправить сообщение пользователю",
            "Отправить файл"
        )
    while True:
        Menu.menu(menu_text)
        choice = Menu.input()

        print()
        if choice == -1:
            print("Неверный ввод. Попробуйте еще раз.")
            continue
        elif choice == 0:
            client.close()
            print("Сессия закрыта")
            break
        elif choice == 1:
            username = input("Ваше имя: ")
            password = input("Пароль: ")
            client.register(username, password)
        elif choice == 2:
            username = input("Ваше имя: ")
            password = input("Пароль: ")
            client.login(username, password)
        elif choice == 3:
            username = input("Ваше имя: ")
            msg = input("Сообщение: ")
            client.send_message_all_users(username, msg)
        elif choice == 4:
            username = input("Ваше имя: ")
            recipient = input("Получатель: ")
            msg = input("Сообщение: ")
            client.send_message(username, recipient, msg)
        elif choice == 5:
            username = input("Ваше имя: ")
            recipient = input("Получатель: ")
            filepath = input("Путь к файлу: ")
            client.send_file(username, recipient, filepath)
        print()


if __name__ == '__main__':
    run()
