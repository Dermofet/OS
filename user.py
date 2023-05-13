from enum import Enum


class UserStatus(Enum):
    INACTIVE = 0
    ACTIVE = 1


class User:
    username: str
    password: str
    status: UserStatus
    incoming_messages: list
    outgoing_messages: list
    address: tuple[str, int] | None

    def __init__(self, username: str, password: str, status: UserStatus, address: tuple):
        self.username = username
        self.password = password
        self.status = status
        self.incoming_messages = []
        self.outgoing_messages = []
        self.address = address

    def __repr__(self):
        return f'User(\n' \
               f'   username={self.username}\n' \
               f'   password={self.password}\n' \
               f'   status={self.status}\n' \
               f'   incoming_messages={self.incoming_messages}\n' \
               f'   outgoing_messages={self.outgoing_messages}\n' \
               f')'
