import ast
import hashlib
import linecache
from collections.abc import Mapping
from contextlib import suppress
from types import SimpleNamespace
from typing import Union, Optional
import uuid
import re
from .flagged_dict import FlaggedDict
from .monkeypath_linecache import monkeypatch_linecache


# Regex to check if code ends with a semicolon
reg_semicol = re.compile(r".*;\s*$", re.DOTALL)

not_found = object()


def gen_sym(varname):
    uuid_str = str(uuid.uuid4()).replace("-", "")
    return f"__{varname}_{uuid_str}__"


def add_asignment_to_last_statement(code: ast.Module, varname: str):
    # If the last statement is not an Expression, don't do anything
    if code.body and isinstance(code.body[-1], ast.Expr):

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


def runcode(
    code: Union[str, ast.Module],
    namespace: Optional[Union[SimpleNamespace, Mapping]] = None,
    readonly_namespace: Optional[Union[SimpleNamespace, Mapping]] = None,
):
    """
    Execute Python code in a namespace and return the result of the last statement in the code.

    Args:
        code (Union[str, ast.Module]): The code to execute.
        namespace (Union[SimpleNamespace, Mapping], optional): The namespace to execute
            the code in. Defaults to None.
        readonly_namespace (Union[SimpleNamespace, Mapping], optional): The namespace to
            execute the code in. Defaults to None.

    Returns:
        Any: The result of the last statement in the code. If that statement is not an
            expression None is returned.

    """
    get_namespace_mapping = (
        lambda x: {} if x is None else x if isinstance(x, Mapping) else x.__dict__
    )
    nspace = get_namespace_mapping(namespace)

    # __builtins__ gets automatically injected by exec, remove it if it's not already there
    remove_builtins_from_namespace = "__builtins__" not in nspace

    # Combine the namespaces into one and flag the read/write ones
    ns_exec = FlaggedDict(nspace, __flags__=nspace)
    ns_exec.update(get_namespace_mapping(readonly_namespace))

    # Return the last statement to this unique variable
    var_return = gen_sym("return")

    # Create a fake traceback file to display the correct number of the error
    filename = f"runcode-{hashlib.sha1(str(code).encode('utf-8')).hexdigest()}"

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
        # `SyntaxError` from `compile` is in higher traceback than errors from `exec`
        if isinstance(e, SyntaxError):
            e.filename = filename
            lineno = e.lineno
        else:
            lineno = e.__traceback__.tb_next.tb_lineno

        # Inject fake file contents to traceback cache
        if isinstance(code, str):
            # Python 3.11 has new functionality to display traceback notes
            if hasattr(e, "add_note"):
                e.add_note(format_code_for_error_line_display(code, lineno))

        monkeypatch_linecache(filename, code)

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
