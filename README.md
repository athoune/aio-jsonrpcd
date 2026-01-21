# Jsonrpc server

[Jsonrpc specification](https://www.jsonrpc.org/specification)

## Testing it

Server:

    python -m jsonrpcd.ws.hello

Client:

The client is almost interactive, you have to write your message, a JSON, in this demo.

    python client.py http://0.0.0.0:8080/rpc
    -> {"method":"hello","id":42, "jsonrpc":"2.0", "params":["bob"]}
