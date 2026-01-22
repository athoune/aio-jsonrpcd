import jwt


def encode(login: str, room: str, key: str) -> str:
    return jwt.encode(dict(login=login, room=room), key, algorithm="HS256")


if __name__ == "__main__":
    import sys
    import os

    size = 4
    key = os.getenv("FAN_KEY")
    if key is not None:
        size = 3

    if len(sys.argv) != size:
        print("Error:\npython -m jsonrpcd.fan.cli login room key")
    else:
        if key is None:
            login, room, key = sys.argv[1:]
        else:
            (login, room) = sys.argv[1:]
        token = encode(login, room, key)
        print(f"""login: {login}
room: {room}
token:
{token}
""")
