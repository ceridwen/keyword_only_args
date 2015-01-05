#!/usr/bin/python

from __future__ import print_function

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import functools
import inspect


def decorator_closure(*included_keywords):
    """Transforms a function with keyword arguments into one with
    keyword-only arguments.

    Call this decorator as @keyword_only_args() for the default mode,
    which makes all keyword arguments keyword-only, or with the names
    of arguments to make keyword-only.  They must correspond with the
    names of arguments in the decorated function.  It works by
    collecting all the arguments into *args and **kws, then moving the
    arguments marked as keyword-only from **kws into *args.

    Args:
      *included_keywords: Keyword-only arguments as strings.

    Returns:
      A decorator that modifies a function so it has keyword-only
      arguments.

    """
    def decorator(func):
        """Decorator factory, assigns arguments as keyword-only and
        calculates sets for error checking.

        Args:
          func: The function to decorate.

        Returns:
          A function wrapped so that it has keyword-only arguments. 
        """
        positional_args, _, _, defaults = inspect.getargspec(func)
        args_with_defaults = set(positional_args[len(defaults):])
        kw_only_args = set(included_keywords) if included_keywords else args_with_defaults.copy()
        args_defaults = list(zip_longest(reversed(positional_args), reversed(defaults)))
        args_defaults.reverse()
        positional_args = set(positional_args)

        @functools.wraps(func)
        def wrapper(*args, **kws):
            """The decorator itself, checks arguments with set operations, moves
            args from *args into **kws, and then calls func().

            Args:
              *args, **kws: The arguments passed to the original function.

            Returns:
              The original function's result when it's called with the
              modified arguments.

            Raises:
              TypeError: When there is a mismatch between the supplied
                and expected arguments.

            """
            keys = set(kws)
            # Are all the keyword-only args covered either by a passed
            # argument or a default?
            if not kw_only_args <= keys | args_with_defaults:
                wrong_args(func, args_defaults, kw_only_args - (keys | args_with_defaults), 'keyword-only')
            # Are there enough positional args to cover all the
            # arguments not covered by a passed argument or a default?
            if len(args) < len(positional_args - (keys | args_with_defaults)):
                wrong_args(func, args_defaults, positional_args - (keys | args_with_defaults), 'positional', len(args))

            args = list(args)
            for index, (name, default) in enumerate(args_defaults):
                if name in kw_only_args or name in keys & positional_args:
                    args.insert(index, kws.pop(name, default))
            func(*args, **kws)
        return wrapper

    def wrong_args(func, args_defaults, missing_args, arg_type, number_of_args=0):
        """ Raise Python 3-style TypeErrors for missing arguments."""
        ordered_args = [a for a, _ in args_defaults if a in missing_args]
        ordered_args = ordered_args[number_of_args:]
        error_message = ['%s() missing %d required %s argument' % (func.__name__, len(ordered_args), arg_type)]
        if len(ordered_args) == 1:
            error_message.append(": '%s'" % ordered_args[0])
        else:
            error_message.extend(['s: ', ' '.join("'%s'" % a for a in ordered_args[:-1]), " and '%s'" % ordered_args[-1]])
        raise TypeError(''.join(error_message))

    return decorator


if __name__ == '__main__':
    def test(f, *args, **kws):
        print(args, kws, '-> ', end='')
        try:
            f(*args, **kws)
        except TypeError as e:
            print(e.args[0])

    @keyword_only_args('c')
    def f(a, b, c='c', d='d', *args, **kws):
        print(a, b, c, d, args, kws)

    test(f)
    test(f, 0, 1)
    test(f, -1, b='b')
    test(f, b='b')
    test(f, 0)
    test(f, 0, 1, 2, 3, 4, 5, c='foo', d='bar', e='baz')

    @keyword_only_args('b', 'c')
    def f(a, b, c='c', d='d', *args, **kws):
        print(a, b, c, d, args, kws)

    test(f, 0)
    test(f, 0, b='b')
    test(f, 0, 1, 2)
    test(f, 0, 1, 2, b='b')
    test(f, 0, 1, 2, 3, 4, 5, c='foo', d='bar', e='baz')
    test(f, 0, 1, 2, 3, 4, 5, b='foo', c='bar', e='baz')

    class C(object):
        @keyword_only_args('b', 'c')
        def __init__(self, a, b, c='c', d='d', *args, **kws):
            print(a, b, c, d, args, kws)

    test(C, 0, 1, 2, b='b')
    test(C, 0, 1, 2, 3, 4, 5, b='foo', c='bar', e='baz')
