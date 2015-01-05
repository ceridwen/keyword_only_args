## Synopsis

Decorator implementing keyword-only arguments in Python
2.x. Compatible with 3.x code.

## Code Example

Call the decorator with the names of the arguments to make
keyword-only as strings:

````Python
@keyword_only_args('c')
def f(a, b, c='c', d='d', *args, **kws):
````

This will make it so that f() accepts c only as a keyword.

To make a keyword-only argument without a default value, assign a
positional argument as keyword-only:

````Python
@keyword_only_args('b', 'c')
def f(a, b, c='c', d='d', *args, **kws):
````

This will make b and c keyword-only, with no default for b.

When called without arguments, the decorator will make all keyword
arguments keyword-only:

````Python
@keyword_only_args()
def f(a, b, c='c', d='d', *args, **kws):
````

This will make c and d keyword-only.
