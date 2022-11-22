import linecache
from contextlib import contextmanager
from time import time

_cache = {}

_checkcache = linecache.checkcache


def _checkcache_monkeypatch(filename=None):
    if filename in _cache:
        linecache.cache[filename] = _cache[filename]

    if filename is None:
        # clear entries
        _checkcache(filename)

        for key, value in _cache.items():
            # re-add all missing entries
            linecache.cache[key] = value

    elif filename not in _cache:
        _checkcache(filename)


_updatecache = linecache.updatecache


def _updatecache_monkeypatch(filename, **kwargs):

    if filename in _cache:
        linecache.cache[filename] = _cache[filename]
        return _cache[filename][2]
    else:
        return _updatecache(filename, **kwargs)


def monkeypatch_linecache(filename, code):
    checkcache = linecache.checkcache
    updatecache = linecache.updatecache

    if isinstance(code, str):
        _cache[filename] = (
            len(code),
            time(),
            [i+'\n' for i in code.splitlines()],
            filename,
        )

        linecache.checkcache = _checkcache_monkeypatch
        linecache.updatecache = _updatecache_monkeypatch
