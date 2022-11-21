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
from .reserve_dict import ReserveDict


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

    ns_exec = ReserveDict.fromdicts(ns, ro_ns)

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

    # Clean up the namespace
    return_value = ns_exec.pop(var_return, None)

    return return_value
