import jwt


def encode(login: str, room: str, key: str) -> str:
    return jwt.encode(dict(login=login, room=room), key, algorithm="HS256")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Error:\npython -m jsonrpcd.fan.cli login room key")
    else:
        login, room, key = sys.argv[1:]
        print(encode(login, room, key))
