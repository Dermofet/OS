from client import Client
from typing import Union
import os.path


class Menu:
    @staticmethod
    def display_menu(menu_text: Union[str, list[str], tuple[str]]):
        if isinstance(menu_text, str):
            print(menu_text)
        elif isinstance(menu_text, (list, tuple)):
            for i, string in enumerate(menu_text):
                print(f'{i}. {string}')

    @staticmethod
    def get_user_input() -> int:
        try:
            return int(input("Ваш выбор: "))
        except ValueError:
            return -1

    @staticmethod
    def get_directory_from_user():
        while True:
            filepath = input("Введите папку, в которой будут сохраняться файлы: ")
            if os.path.isdir(filepath):
                return os.path.abspath(filepath)
            print("Такой папки не существует. Попробуйте еще раз.")

    @staticmethod
    def run(server_address, client_address: tuple = None):
        try:
            client = Client(server_address=server_address, client_address=client_address)
            client.download_dir = Menu.get_directory_from_user()
            menu_text = (
                "Выход",
                "Регистрация",
                "Вход",
                "Отправить сообщение всем пользователям",
                "Отправить сообщение пользователю",
                "Отправить файл",
                "Директория для скачивания"
            )
            while True:
                print()
                Menu.display_menu(menu_text)
                choice = Menu.get_user_input()

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
                    msg = input("Сообщение: ")
                    client.send_message_all_users(msg)
                elif choice == 4:
                    recipient = input("Получатель: ")
                    msg = input("Сообщение: ")
                    client.send_message_to_user(recipient, msg)
                elif choice == 5:
                    recipient = input("Получатель: ")
                    filepath = input("Путь к файлу: ")

                    if not os.path.exists(filepath):
                        print("Файл не существует")
                        continue
                    if os.path.isdir(filepath):
                        print("Это директория, не файл")
                        continue
                    client.send_file(recipient, filepath)
                elif choice == 6:
                    print(f"Директория: {client.download_dir}")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    Menu.run(server_address=("127.0.0.1", 8888))
