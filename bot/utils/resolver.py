from importlib import import_module
from pkgutil import walk_packages
from typing import Any, Iterator, NoReturn

from bot import cogs


def find_available_cogs() -> Iterator[Any]:
    """
    Yields all available cogs from the bot.cogs package
    """

    def on_error(name: str) -> NoReturn:
        raise ImportError(name=name)

    for module in walk_packages(cogs.__path__, cogs.__name__ + ".", onerror=on_error):
        # Excludes private packages
        *_, unqualified = module.name.rpartition(".")
        if module.ispkg or unqualified.startswith("_"):
            continue
        imported = import_module(module.name)
        # Checks if it have a setup function (a callable)
        if callable(getattr(imported, "setup", None)):
            yield imported


COGS = frozenset(find_available_cogs())
