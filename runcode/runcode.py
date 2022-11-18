import ast
import hashlib
import linecache
from collections.abc import Mapping
import time
from contextlib import suppress
from types import SimpleNamespace
from typing import Union, Optional
import uuid
import re
from itertools import chain


# Regex to check if the last expression ends with a semicolon
reg_semicol = re.compile(r".*;\s*$", re.DOTALL)

not_found = object()


def gen_sym(varname):
    uuid_str = str(uuid.uuid4()).replace("-", "")
    return f"__{varname}_{uuid_str}__"


def add_asignment_to_last_expression(code: ast.Module, varname: str):
    assign = ast.parse(f"{varname}=None").body[0]
    last_expression = getattr(code.body[-1], "value", code.body[-1])

    assign.value = last_expression
    for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
        setattr(assign, attr, getattr(code.body[-1], attr))

    code.body[-1] = assign


def format_code_for_error_line_display(code: str, lineno: int):
    lineno = int(lineno)
    strlineno = str(lineno)

    lines = code.splitlines()
    lines_annotated = [f"{i+1:7d} {line}" for i, line in enumerate(lines)]
    lines_annotated[lineno - 1] = (
        ("-") * (5 - len(strlineno)) + "> " + strlineno + " " + lines[lineno - 1]
    )
    return "\n".join(lines_annotated)


class DualDict(dict):
    def __init__(self, mutable_dict, immutable_dict=None):
        self.mutable_dict = mutable_dict
        self.immutable_dict = {} if immutable_dict is None else immutable_dict
        self.immutable_blacklist = set(mutable_dict)

    def __setitem__(self, key, value):
        self.mutable_dict.__setitem__(key, value)
        if key in self.immutable_dict:
            self.immutable_blacklist.add(key)

    def __getitem__(self, key):
        val = self.mutable_dict.get(
            key,
            not_found
            if key in self.immutable_blacklist
            else self.immutable_dict.get(key, not_found),
        )
        if val is not_found:
            raise KeyError(key)

        return val

    def __iter__(self):
        return chain(
            iter(self.mutable_dict),
            (i for i in self.immutable_dict if i not in self.immutable_blacklist),
        )

    # def __eq__(self, other):
    #     if not isinstance(other, DualDict):
    #         return NotImplemented
    #     return (
    #         self.mutable_dict == other.mutable_dict
    #         and self.immutable_dict == other.immutable_dict
    #         and self.immutable_blacklist == other.immutable_blacklist
    #     )

    # def __hash__(self):
    #     return hash((self.mutable_dict, self.immutable_dict, self.immutable_blacklist))

    ## Probably the most expensive operation
    # def __len__(self):
    #    return len(
    #        set(self.mutable_dict).union(
    #            set(self.immutable_dict).difference(self.immutable_blacklist)
    #        )
    #    )

    def __repr__(self):
        return f"{type(self).__name__}(mutable_dict={self.mutable_dict}, immutable_dict={self.immutable_dict}, immutable_blacklist={self.immutable_blacklist})"

    def pop(self, key, default=not_found):
        if (val := self.mutable_dict.pop(key, not_found)) is not not_found:
            pass
        elif (
            key not in self.immutable_blacklist
            and (val := self.immutable_dict.pop(key, not_found)) is not not_found
        ):
            pass

        if val is not_found:
            if default is not_found:
                raise KeyError(key)
            return default

        return val

    def __delitem__(self, key):
        self.pop(key)

    def get(self, key, default=None):
        return self.mutable_dict.get(
            key,
            default
            if key in self.immutable_blacklist
            else self.immutable_dict.get(key, default),
        )

    def __contains__(self, key):
        return key in self.mutable_dict or (
            key not in self.immutable_blacklist and key in self.immutable_dict
        )

    def clear(self):
        self.mutable_dict.clear()
        self.immutable_blacklist.union(self.immutable_dict)

    def update(self, **args):
        for d in args:
            self.mutable_dict.update(d)
            self.immutable_blacklist.union(self.immutable_dict)


def runcode(
    code: Union[str, ast.Module],
    namespace: Optional[Union[SimpleNamespace, Mapping]] = None,
    readonly_namespace: Optional[Union[SimpleNamespace, Mapping]] = None,
):
    """
    Execute Python code in a namespace and return the result of the last expression.

    Args:
        code (Union[str, ast.Module]): The code to execute.
        namespace (Union[SimpleNamespace, Mapping], optional): The namespace to execute
            the code in. Defaults to None.
        readonly_namespace (Union[SimpleNamespace, Mapping], optional): The namespace to
            execute the code in. Defaults to None.

    Returns:
        Any: The result of the last expression, unless `code` ends with a semicolon, in
            which case None is returned.

    """
    get_namespace_mapping = (
        lambda x: {} if x is None else x if isinstance(x, Mapping) else x.__dict__
    )
    ns = get_namespace_mapping(namespace)
    ro_ns = get_namespace_mapping(readonly_namespace)

    var_return = gen_sym("return")

    ns_exec = DualDict(ns, ro_ns)

    filename = f"<runcode-{hashlib.sha1(str(code).encode('utf-8')).hexdigest()}>"

    # Set up the AST node
    runme = code

    # If a syntax error occurs, we want it to be raised at the exec/compile stage
    with suppress(SyntaxError):
        if not isinstance(runme, ast.AST):
            runme = ast.parse(runme)

        if isinstance(code, ast.AST) or not reg_semicol.match(code):
            if isinstance(runme.body[-1], ast.Expr):
                add_asignment_to_last_expression(runme, var_return)

    # Execute the annotated AST node
    try:
        exec(compile(runme, filename, "exec"), ns_exec)
    except Exception as e:
        # SyntaxError occurs a traceback higher (before the code is exec)
        if isinstance(e, SyntaxError):
            e.filename = filename
            lineno = e.lineno
        else:
            lineno = e.__traceback__.tb_next.tb_lineno

        # Python 3.11 will have a new function to display traceback notes - we can add the code here.
        if isinstance(code, str):
            if filename not in linecache.cache:
                linecache.cache[filename] = (
                    len(code),
                    time.time(),
                    code.splitlines(),
                    filename,
                )

            e.__notes__ = getattr(e, "__notes__", [])
            e.__notes__.append(format_code_for_error_line_display(code, lineno))
        raise

    #print(ns_exec)

    # Clean up the namespace
    return_value = ns_exec.pop(var_return, None)

    return return_value
