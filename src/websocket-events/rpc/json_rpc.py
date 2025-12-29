from typing import Callable


class Dispatcher:
    """Find a method by its name"""

    def __init__(self):
        self.methods = dict[str, Callable]()
        self.namespaces = dict[str, Callable]()

    def register(self, key: str, action: Callable) -> None:
        self.methods[key] = action

    def __getitem__(self, key: str) -> Callable:
        m: None | Callable = self.methods.get(key)
        if m is not None:
            return jsonrpc_wrapper(m)
        else:
            raise Exception(f"method {key} is not found")
        """
        ns = key.split(".")[0]
        # FIXME how can I pass the complete key to ne namespace handler ?
        return jsonrpcize(self.namespaces[ns])
        """


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
