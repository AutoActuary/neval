# runcode

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
 

### runcode alternative scoping

The main difference is that `runcode` has two arguments called `namespace`
(almost like `locals`) for reflecting scope changes and `namespace_readonly`
(almost like `globals`) to additionally draw from. The main deviations are:
- `namespace` is a `dict` whose keys are read and written to reflect scope
  changes
- `namespace_readonly` is a `dict` whose keys are only read, but not written
- if the last statement in the code is an expression, the executed value is returned
- the line number and line text are displayed in the traceback (unlike `exec`)
- for Python >= 3.11 the traceback includes the  similar to `ipython`
```python
File <runcode-f19665a526a8ddf7663dfc0f904b1e507b5005cf>:3
      1 a = 1
----> 2 b = a/0

ZeroDivisionError: division by zero
```
