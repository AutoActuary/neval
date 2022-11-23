import ast
import uuid
from pathlib import Path
from types import SimpleNamespace


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


def format_code_for_error_line_display(code: str, lineno: int, filename: str):
    lineno = int(lineno)
    strlineno = str(lineno)

    lines = code.splitlines()
    lines_annotated = [f"{i+1:7d} {line}" for i, line in enumerate(lines)]
    lines_annotated[lineno - 1] = ("-") * (5 - len(strlineno)) + "> " + strlineno + " " + lines[lineno - 1]
    return "\n".join([f"Error in {Path(filename).name}:"] + lines_annotated)


def deepest_traceback(traceback, filename):
    pointer = SimpleNamespace(tb_next=traceback)
    tb_find = None
    while (getattr(pointer, "tb_next", None)) is not None:
        pointer = pointer.tb_next
        if pointer.tb_frame.f_code.co_filename == filename:
            tb_find = pointer

    return tb_find
