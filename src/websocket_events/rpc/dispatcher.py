from typing import Callable


class Dispatcher[T: Callable]:
    # Callable[..., Awaitable[tuple["Request", dict[str, Any]]]]
    _handlers: dict[str, T]
    _namespaces: dict[str, T]

    def __init__(self) -> None:
        self._handlers = dict[str, T]()
        self._namespaces = dict[str, T]()

    def put_handler(self, name: str, handler: T):
        self._handlers[name] = handler

    def put_namespace(self, name: str, handler: T):
        self._namespaces[name] = handler

    def __getitem__(self, name: str) -> T:
        slugs = name.split(".")
        if len(slugs) > 1 and slugs[0] in self._namespaces:
            return self._namespaces[slugs[0]]
        return self._handlers[name]
