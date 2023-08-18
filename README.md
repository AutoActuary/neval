# NEval — Namespaced Code Evaluator

This package provides an alternative scoping mechanism
to the standard `exec` and `eval` functions for running raw Python code. 
The goal is to overcome the following behavior of `exec`, as described
in the [docs](https://docs.python.org/3/library/functions.html#exec): 
> If `exec` gets two separate objects as `globals` and `locals`, the code will
> be executed as if it were embedded in a class definition.

For instance, when you want to use `locals` as the mutable scope and 
`globals` as additional lookup, the default `exec` and `eval` procedures
result in unexpected behavior. For example:

```python
# ✓ [1]
exec("a=[1]; print([i for i in a])", {}, {})

# ✗ NameError: name 'a' is not defined
exec("a=[1]; print([i for i in a if a])", {}, {})

# ✓ os
exec("import os; print(os.__name__)", {}, {})
 
# ✗ NameError: name 'os' is not defined
exec("import os; (lambda: print(os.__name__))()", {}, {})
```
 

### NEval's alternative evaluation

The main difference is that `neval` has two arguments called `namespace` 
and `namespace_readonly` instead of `locals` and `globals`. These are similar
to `locals` and `globals` but with a slightly different implementation under 
the hood to allow for deviations from `eval` and `exec`.

Key features of `neval` include:
- `namespace` is a `dict` or an object with a `__dict__` attribute. This object is  
      read/write in order to reflect all scope changes happening during execution.
      This is helpful in keeping track of pipelines with many side effects.
- `namespace_readonly` is a `dict` or an object with a `__dict__` attribute. Note
      that the dictionary is treated as read-only in the sense that no objects
      will be added, no objects will be removed, and no objects will be replaced,
      although objects can be accessed and mutated. A common use case to set this 
      parameter as `globals()` to make use of global variables and imported modules
      without changing the global state.
- `neval` returns the value of the last section in your code. If the last section is
      an expression, it will return the executed value, if its a statement (such as
      assignments of function declarations) it will return `None`.
- If an error occurs, a full traceback is generated along with a temporary code file
      to facilitate the whole process.
- For Python >= 3.11, the traceback also includes a full printout of the code by making
     use of the new `Exception.add_note` feature. The aim is to mimic the helpful error
     feedback of `ipython`.
```python
  File "/temp/neval-057d58343544b6d102cac201bdc11527a0224e87", line 2, in <module>
    c = 4/0
        ~^~
ZeroDivisionError: division by zero
Error in neval-057d58343544b6d102cac201bdc11527a0224e87:
      1 a = 1
----> 2 b = 4/0
      3 c = 5
```


### Examples

```python
from neval import neval

neval("a = 1; b = 2; c = 3; d = 4; a + b + c + d")
# ✓ 10

ns = {}
neval("a = 1; b = 2; c = 3; d = 4; a + b + c + d", ns)
# ✓ 10

ns
# ✓ {'a': 1, 'b': 2, 'c': 3, 'd': 4}

import numpy
from types import SimpleNamespace

ns = SimpleNamespace()
neval("a = argmax(array([1,2,3,4,3,2,1])**2)", ns, numpy)

ns.a
# ✓ 3

ns = SimpleNamespace()
a, b, c = 1, 2, 3
neval("d = a + b*2 + c*3", ns, globals())

ns.d
# ✓ 14

d
# ✗ NameError: name 'd' is not defined

neval("d = a + b*2 + c*3", globals())

d
# ✓ 14

params = SimpleNamespace(a=1, b=2, c=3)

neval("d = a + b*2 + c*3", params)

params
# ✓ namespace(a=1, b=2, c=3, d=14)

neval("""\
a = 1 + 2
this is incorrect
b = a + 3
""")
# ✗ NameError: name 'this' is not defined
#   Error in neval-8efcb70d4b63817f9fd92f3b61eb5a7c0c45cfe9:
#         1 a = 1 + 2
#   ----> 2 this is incorrect
#         3 b = a + 3

```
