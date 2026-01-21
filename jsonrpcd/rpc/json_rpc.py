from typing import Any, Callable


class RPCException(Exception):
    pass


def jsonrpc_wrapper(raw: Callable) -> Callable:
    """
    Transform a plain old async function to a function with a
    jsonrpc method as input, a jsonrpc response as output
    """

    async def a(args: dict) -> dict | None:
        params = args.get("params", None)
        try:
            if params is None:
                resp = await raw()
            elif isinstance(params, list):
                resp = await raw(*params)
            elif isinstance(params, dict):
                resp = await raw(**params)
            else:
                raise Exception(f"Unknown argument format : {type(params)}")
            if "id" not in args:
                if resp is not None:
                    raise RPCException(f"Notification must return None not {resp}")
                return None
            return dict(result=resp, id=args["id"], jsonrpc=args["jsonrpc"])
        except RPCException as e:
            raise e
        except Exception as e:
            if "id" not in args:
                return None
            return dict(
                error=dict(code=-32000, message=str(e)),
                id=args["id"],
                jsonrpc=args["jsonrpc"],
            )

    return a


class JsonRpcRequestException(Exception):
    pass


def checkup(message: dict[str, Any]):
    if message.get("jsonrpc") != "2.0":
        raise JsonRpcRequestException(
            f'jsonrpc version must be "2.0" not {message.get("jsonrpc")}'
        )
    if "method" not in message:
        raise JsonRpcRequestException("Method is mandatory")
    if "params" not in message:
        message["params"] = []
