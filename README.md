# neval — Namespaced code evaluator     

This package provides an alternative scoping mechanism
to the standard `exec` and `eval` functions for running raw Python code. 
The goal is to overcome the following behaviour of `exec`, as describe
in the [docs](https://docs.python.org/3/library/functions.html#exec): 
> If exec gets two separate objects as globals and locals, the code will
> be executed as if it were embedded in a class definition.

For instance, when you want to use `locals` as a _staging_ scope and 
`globals` as an accessible backdrop, the executed code can quickly
result in unexpected behaviour. For example:

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
 

### Runcode's alternative evaluation

The main difference is that `neval` has two arguments called `namespace` 
for reflecting scope changes (almost like `locals`) and `namespace_readonly`
to additionally draw from (almost like `globals`). The main deviations are:
- `namespace` is a `dict` or a `__dict__` attributed object whose keys are 
      read and written to reflect scope changes
- `namespace_readonly` is a `dict` or a `__dict__` attributed object whose
      keys are only read, but not written
- if the last statement in the code is an expression, the executed value of 
      the expression is returned
- if an error occurs, a temp file is generated in order for C interpreter to 
      provide a more informative error message (after Python teardown)
- for Python >= 3.11 the traceback includes a printout of the code using the new 
     `add_note` feature, similarly to `ipython` 
```python
  File "/temp/neval-057d58343544b6d102cac201bdc11527a0224e87", line 3, in <module>
    c = 4/0
        ~^~
ZeroDivisionError: division by zero
Error in neval-057d58343544b6d102cac201bdc11527a0224e87:
      1 a = 1
----> 3 b = 4/0
      4 c = 5
```


### Examples

```python
from neval import neval

neval("a = 1; b = 2; c = 3; d = 4; a + b + c + d")
# ✓ 10

neval("a = 1; b = 2; c = 3; d = 4; a + b + c + d", ns:={})
# ✓ 10

ns
# ✓ {'a': 1, 'b': 2, 'c': 3, 'd': 4}

import numpy as np
from types import SimpleNamespace

neval("a = argmax(array([1,2,3,4,3,2,1])**2)", ns:=SimpleNamespace(), np)

ns.a
# ✓ 3

a,b,c = (1,2,3)

neval("d = a + b*2 + c*3", ns:=SimpleNamespace(), globals())

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
