# Fireworks demo

## Install jsronrpcd in its virtual env

    poetry install
    source ./.venv/bin/activate

## Create tokens

The room name is hardcoded : *secret_room*

    FAN_KEY="my super secret key" python -m jsonrpcd.fan.cli alice secret_room
    FAN_KEY="my super secret key" python -m jsonrpcd.fan.cli bob secret_room

## Launch the server

    FAN_KEY="my super secret key" ./server.py

## Web browser

Pick two web browsers, two tabs, whatever handles HTML, javascript and websocket.

http://localhost:8080

Auth with the tokens, then send fireworks.
Sender doesn't see anything (open the javascript console), but all other connected users can enjoy the fireworks.
