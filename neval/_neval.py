import ast
import hashlib
import linecache
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace
from typing import Union, Optional, Any
import re
from .flagged_dict import FlaggedDict
from .util import (
    gen_sym,
    add_asignment_to_last_statement,
    deepest_traceback,
    format_code_for_error_line_display,
)

reg_neval_filename = re.compile(r"neval-[0-9a-f]{40}")
neval_filename_cache = {}


def neval(
    code: Union[str, ast.Module],
    namespace: Optional[Union[Mapping, SimpleNamespace, Any]] = None,
    namespace_readonly: Optional[Union[Mapping, SimpleNamespace, Any]] = None,
    traceback_file_output: bool = True,
) -> Any:
    """
    Execute Python code in a namespace and return the result of the last statement in the code.

    Args:
        code (Union[str, ast.Module]): The code to execute.
        namespace (Union[Mapping, Any], optional): The namespace to execute the code in, this can either be a `dict` or
            any object with a `__dict__` attribute such as `SimpleNamespace`. Defaults to `None`.
        namespace_readonly (Union[Mapping, Any], optional): A namespace to execute the code in, this can
            either be a `dict` or any object with a `__dict__` attribute such as `SimpleNamespace`. Defaults to `None`.
        traceback_file_output (bool, optional): Option to dump the `code` string to a temporary file when an error
            occurs in order for the Python stacktrace to print all relevant lines. Ideally this should be mocked in
            memory, but it seems like there are some redundancies in the interpreter that doesn't make this process
            easy. This might cause security issues. Defaults to `True`.


    Returns:
        Any: The result of the last statement in the code. If that statement is not an expression None is returned.

    """

    def get_namespace_mapping(x):
        return {} if x is None else x if isinstance(x, Mapping) else x.__dict__

    nspace = get_namespace_mapping(namespace)

    # __builtins__ gets automatically injected by exec, remove it if it's not already there
    remove_builtins_from_namespace = "__builtins__" not in nspace

    # Combine the namespaces into one and flag the read/write ones
    ns_exec = FlaggedDict(nspace, __flags__=nspace)
    ns_exec.update(get_namespace_mapping(namespace_readonly))

    # Return the last statement to this unique variable
    var_return = gen_sym("return")

    # Create a fake traceback file to display the correct number of the error
    filename = Path(
        tempfile.gettempdir() if traceback_file_output else "",
        f"neval-{hashlib.sha1(str(code).encode('utf-8')).hexdigest()}",
    ).as_posix()
    neval_filename_cache[Path(filename).name] = filename

    # Set up the AST node
    runme = code

    # If a syntax error occurs, rather raise it at the exec line
    with suppress(SyntaxError):
        if not isinstance(runme, ast.AST):
            runme = ast.parse(runme)

        add_asignment_to_last_statement(runme, var_return)

    # Execute the annotated AST node
    try:
        exec(compile(runme, filename, "exec"), ns_exec)

    # If an error occurs, display it properly
    except Exception as e:
        lineno = None

        # `SyntaxError` is special since it is thrown by `compile` and not `exec`
        if isinstance(e, SyntaxError):
            e.filename = filename
            lineno = e.lineno

        # Inject fake file contents to traceback cache
        if isinstance(code, str):
            # Python 3.11 has new functionality to display traceback notes
            if hasattr(e, "add_note"):
                if lineno is None:
                    if tb_last := deepest_traceback(e.__traceback__, filename):
                        lineno = tb_last.tb_lineno
                if lineno is not None:
                    e.add_note(
                        format_code_for_error_line_display(code, lineno, filename),
                    )

        # Add content to temp in order for C to print the correct line number after Python teardown
        if traceback_file_output and isinstance(code, str):
            for fname in Path(tempfile.gettempdir()).glob("neval-*"):
                if reg_neval_filename.match(fname.name) and fname.name not in neval_filename_cache:
                    fname.unlink()

            Path(filename).write_text(code)

        raise

    # Even if an error occurs, ensure that mutated scope is reflected in the namespace
    finally:
        return_value = ns_exec.pop(var_return, None)
        if remove_builtins_from_namespace:
            ns_exec.pop("__builtins__", None)

        nspace.clear()

        for key in ns_exec.flags:
            nspace[key] = ns_exec[key]

    linecache.cache.pop(filename, None)

    return return_value
