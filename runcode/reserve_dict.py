from __future__ import annotations
from collections.abc import ItemsView, KeysView, ValuesView
from typing import Any, Tuple
from itertools import chain

NotFound = object()


class ChainItemsView(ItemsView):
    def __init__(self, *args: dict): # noqa
        self._args = args

    def __iter__(self):
        return chain(*(arg.items() for arg in self._args))

    def __len__(self):
        return sum(len(arg) for arg in self._args)

    def __contains__(self, item):
        return any(item in arg.items() for arg in self._args)


class ChainKeysView(KeysView):
    def __init__(self, *args: dict): # noqa
        self._args = args

    def __iter__(self):
        return chain(*(arg.keys() for arg in self._args))

    def __len__(self):
        return sum(len(arg) for arg in self._args)

    def __contains__(self, item):
        return any(item in arg.keys() for arg in self._args)


class ChainValuesView(ValuesView):
    def __init__(self, *args: dict): # noqa
        self._args = args

    def __iter__(self):
        return chain(*(arg.values() for arg in self._args))

    def __len__(self):
        return sum(len(arg) for arg in self._args)

    def __contains__(self, item):
        return any(item in arg.values() for arg in self._args)


class ReserveDict(dict):
    def __init__(self, seq=NotFound, __reserve_dict__=None, **kwargs):  # noqa
        reserve = __reserve_dict__ if __reserve_dict__ else {}

        if seq is not NotFound:
            self.d = dict(seq, **kwargs)
        else:
            self.d = dict(**kwargs)

        self.reserve = {key: value for key, value in reserve if key not in self.d}

    @classmethod
    def fromdicts(cls, d, reserve):
        reserve_dict = cls()
        reserve_dict.d = d
        reserve_dict.reserve = {
            key: value for key, value in reserve.items() if key not in reserve_dict.d
        }
        return reserve_dict

    @classmethod
    def fromkeys(cls, *args, **kwargs) -> ReserveDict:
        return cls.fromdicts(dict.fromkeys(*args, **kwargs), {})

    def clear(self) -> None:
        self.d.clear()
        self.reserve.clear()

    def copy(self) -> ReserveDict:
        d = self.d.copy()
        reserve = self.reserve.copy()
        return self.fromdicts(d, reserve)

    def get(self, key, default=None) -> Any:
        return self.d.get(key, self.reserve.get(key, default))

    def items(self) -> ChainItemsView:
        return ChainItemsView(self.reserve, self.d)

    def keys(self) -> ChainKeysView:
        return ChainKeysView(self.reserve, self.d)

    def values(self) -> ChainValuesView:
        return ChainValuesView(self.reserve, self.d)

    def pop(self, k, d=NotFound) -> Any:
        try:
            return self.d.pop(k)
        except KeyError:
            if d is NotFound:
                return self.reserve.pop(k)
            else:
                return self.reserve.pop(k, d)

    def popitem(self) -> Tuple[Any, Any]:
        try:
            return self.d.popitem()
        except KeyError:
            return self.reserve.popitem()

    def setdefault(self, key, value=None) -> Any:
        try:
            self.reserve[key]
        except KeyError:
            return self.d.setdefault(key, value)

    def update(self, *args) -> None:
        for arg in args:
            tmp = {}
            tmp.update(arg)

            self.d.update(tmp)
            for key in tmp:
                self.reserve.pop(key, None)

    def __contains__(self, key) -> bool:
        return key in self.d or key in self.reserve

    def __delitem__(self, key) -> None:
        try:
            del self.d[key]
        except KeyError:
            del self.reserve[key]

    def __eq__(self, other) -> bool:
        tmp = {}
        tmp.update(self.reserve)
        tmp.update(self.d)

        return tmp == other

    def __getitem__(self, key) -> Any:
        try:
            return self.d[key]
        except KeyError:
            return self.reserve[key]

    def __iter__(self):
        return chain(self.reserve, self.d)

    def __len__(self) -> int:
        return len(self.d) + len(self.reserve)

    def __ne__(self, other) -> bool:
        return not self == other

    def __repr__(self) -> str:
        tmp = {}
        tmp.update(self.reserve)
        tmp.update(self.d)
        return repr(tmp)

    def __reversed__(self):
        return chain(reversed(self.d), reversed(self.reserve))

    def __setitem__(self, key, value) -> None:
        self.reserve.pop(key, None)
        self.d[key] = value

    def __str__(self) -> str:
        tmp = {}
        tmp.update(self.reserve)
        tmp.update(self.d)
        return str(tmp)

    def __sizeof__(self) -> int:
        return object.__sizeof__(self) + self.d.__sizeof__() + self.reserve.__sizeof__()


r'''
class ReserveDict(dict):
    def __init__(self, seq=NotFound, __reserve_dict__=None, **kwargs):  # noqa
        reserve = __reserve_dict__ if __reserve_dict__ else {}

        if seq is not NotFound:
            self.d = dict(seq, **kwargs)
        else:
            self.d = dict(**kwargs)

        self.reserve = {key: value for key, value in reserve if key not in self.d}

    @classmethod
    def fromdicts(cls, d, reserve):
        reserve_dict = cls()
        reserve_dict.d = d
        reserve_dict.reserve = {
            key: value for key, value in reserve.items() if key not in reserve_dict.d
        }
        return reserve_dict

    @classmethod
    def fromkeys(cls, *args, **kwargs) -> ReserveDict:
        return cls.fromdicts(dict.fromkeys(*args, **kwargs), {})

    def clear(self) -> None:
        self.d.clear()
        self.reserve.clear()

    def copy(self) -> ReserveDict:
        d = self.d.copy()
        reserve = self.reserve.copy()
        return self.fromdicts(d, reserve)

    def get(self, key, default=None) -> Any:
        return self.d.get(key, self.reserve.get(key, default))

    def items(self) -> ChainItemsView:
        return ChainItemsView(self.reserve, self.d)

    def keys(self) -> ChainKeysView:
        return ChainKeysView(self.reserve, self.d)

    def values(self) -> ChainValuesView:
        return ChainValuesView(self.reserve, self.d)

    def pop(self, k, d=NotFound) -> Any:
        try:
            return self.d.pop(k)
        except KeyError:
            if d is NotFound:
                return self.reserve.pop(k)
            else:
                return self.reserve.pop(k, d)

    def popitem(self) -> Tuple[Any, Any]:
        try:
            return self.d.popitem()
        except KeyError:
            return self.reserve.popitem()

    def setdefault(self, key, value=None) -> Any:
        try:
            self.reserve[key]
        except KeyError:
            return self.d.setdefault(key, value)

    def update(self, *args) -> None:
        for arg in args:
            tmp = {}
            tmp.update(arg)

            self.d.update(tmp)
            for key in tmp:
                self.reserve.pop(key, None)

    def __contains__(self, key) -> bool:
        return key in self.d or key in self.reserve

    def __delitem__(self, key) -> None:
        try:
            del self.d[key]
        except KeyError:
            del self.reserve[key]

    def __eq__(self, other) -> bool:
        tmp = {}
        tmp.update(self.reserve)
        tmp.update(self.d)

        return tmp == other

    def __getitem__(self, key) -> Any:
        try:
            return self.d[key]
        except KeyError:
            return self.reserve[key]

    def __iter__(self):
        return chain(self.reserve, self.d)

    def __len__(self) -> int:
        return len(self.d) + len(self.reserve)

    def __ne__(self, other) -> bool:
        return not self == other

    def __repr__(self) -> str:
        tmp = {}
        tmp.update(self.reserve)
        tmp.update(self.d)
        return repr(tmp)

    def __reversed__(self):
        return chain(reversed(self.d), reversed(self.reserve))

    def __setitem__(self, key, value) -> None:
        self.reserve.pop(key, None)
        self.d[key] = value

    def __str__(self) -> str:
        tmp = {}
        tmp.update(self.reserve)
        tmp.update(self.d)
        return str(tmp)

    def __sizeof__(self) -> int:
        return object.__sizeof__(self) + self.d.__sizeof__() + self.reserve.__sizeof__()
'''

