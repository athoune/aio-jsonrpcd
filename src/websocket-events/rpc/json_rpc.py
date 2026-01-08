from typing import Callable, Any, Coroutine


class Dispatcher:
    """Find a method by its name"""

    def __init__(self):
        self.methods = dict[str, Callable]()
        self.namespaces = dict[str, Callable]()

    def register(self, key: str, action: Callable) -> None:
        self.methods[key] = action

    def register_namespace(self, ns: str, action: Callable) -> None:
        self.namespaces[ns] = action

    def __getitem__(self, key: str) -> Callable:
        """Get a jsonrpc wrapped method."""
        ns = key.split(".")[0]
        m: None | Callable = self.methods.get(key)
        if m is not None:
            return m
        n: None | Callable = self.namespaces.get(ns)
        if n is not None:
            return n
        else:
            raise Exception(f"{key} is not a method or part of a namespace")


class JsonRpcDispatcher(Dispatcher):
    def register(self, key: str, action: Callable) -> None:
        return super().register(key, jsonrpc_wrapper(action))

    def __call__(self, request: dict[str, Any]) -> Coroutine:
        return self[request["method"]](request)


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
