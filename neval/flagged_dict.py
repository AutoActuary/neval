from __future__ import annotations
from contextlib import suppress
from typing import Any, List, Iterable, Union


class FlaggedDict(dict):
    def __init__(self, *args, __flags__: Union[List, Iterable] = None, **kwargs):  # noqa
        super().__init__(*args, **kwargs)
        self.flags = {key: None for key in __flags__} if __flags__ else {}

    def clear(self) -> None:
        super().clear()
        self.flags.clear()

    def copy(self) -> FlaggedDict:
        return FlaggedDict(self, __flags__=self.flags)

    def pop(self, k, *args) -> Any:
        with suppress(KeyError):
            self.flags.pop(k)

        return super().pop(k, *args)

    def popitem(self) -> tuple:
        k, v = super().popitem()
        with suppress(KeyError):
            self.flags.pop(k)
        return k, v

    def setdefault(self, k, d=None) -> Any:
        if k not in self:
            self.flags[k] = None

        return super().setdefault(k, d)

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        for k in kwargs:
            self.flags[k] = None

    def __delitem__(self, k) -> None:
        with suppress(KeyError):
            self.flags.pop(k)
        super().__delitem__(k)

    def __repr__(self):
        return f"FlaggedDict({super().__repr__()}, __flags__={list(self.flags.keys())})"

    def __setitem__(self, k, v) -> None:
        self.flags[k] = None
        super().__setitem__(k, v)
