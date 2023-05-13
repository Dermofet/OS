import socket
import time


class Client:
    def __init__(self, IP: str, PORT: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((IP, PORT))

    @staticmethod
    def _recvall(sock):
        BUFF_SIZE = 4096
        data = b''
        while True:
            part = sock.recv(BUFF_SIZE)
            data += part
            if not part:
                break
        return data

    def sendmsg(self, msg):
        msg = str(msg).encode()
        self.sock.sendall(msg)
        return self.getmsg()

    def getmsg(self):
        response = self._recvall(self.sock).decode()
        return response

    def close(self):
        time.sleep(1)  # Добавляем задержку перед закрытием сокета
        self.sock.close()

    def register(self, username, password):
        return self.sendmsg((0, 0, username, password))

    def login(self, username, password):
        return self.sendmsg((1, 0, username, password))

    def send_msg_to_all(self, username, msg):
        return self.sendmsg((2, 2, username, msg))

    def send_msg_to_user(self, sender_username, recipient_username, msg):
        return self.sendmsg((3, 1, sender_username, recipient_username, msg))

    # def send_file_to_user(self, ):


def main():
    client1 = Client('127.0.0.1', 8887)
    # response = client1.sendmsg("aaaaaaaa")
    response = client1.register("Иван", "qwerty")
    print(response)
    client1.close()


if __name__ == '__main__':
    main()
