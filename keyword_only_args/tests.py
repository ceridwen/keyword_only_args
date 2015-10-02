'''This tests the keyword-only arguments decorator using Hypothesis,
generating a function with positional-or-keyword and keyword-only
arguments using Python 3 and the same function using the decorator,
then checking to make sure the output the functions (including that
they both raise a TypeError where expected) is identical.'''

import collections
import inspect
import itertools
import logging
import pprint
import string

import hypothesis
from hypothesis import strategy
from hypothesis import strategies

from keyword_only_args import decorator_factory as keyword_only_args

no_default = object()


@strategies.composite
def parameters(draw):
    '''This Hypothesis strategy generates two OrderedDicts with valid
    parameter names as keys and default values (if any) as values, one
    for the positional-or-keyword arguments for a function and the
    other for keyword-only arguments.  The sets of names are
    guaranteed to be disjoint.  Python has a limit of 255 on the
    number of arguments to a function, so this strategy won't generate
    more parameters than that.

    '''
    # I'm not testing the robustness of Python's argument handling, so
    # my primary concern is generating human-readable parameter names
    # that can't possibly be Python keywords.
    positional_or_kw = draw(strategies.sets(strategies.text(
        alphabet=string.ascii_letters, min_size=1, max_size=3).map(
            lambda s: ''.join(s) + '_'), max_size=255))
    kw_only = draw(strategies.sets(strategies.text(
        alphabet=string.ascii_letters, min_size=1, max_size=3).map(
            lambda s: ''.join(s) + '_'), min_size=1,
                                   max_size=255-len(positional_or_kw)))
    intersection = positional_or_kw & kw_only
    positional_or_kw = frozenset(positional_or_kw - intersection)
    kw_only = frozenset(kw_only - intersection)

    def add_defaults(names):
        defaults = draw(strategies.lists(
            strategies.integers(), max_size=len(names)))
        return collections.OrderedDict(
            itertools.zip_longest(names, defaults, fillvalue=no_default))

    return add_defaults(positional_or_kw), add_defaults(kw_only)

# pprint.pprint(strategy(parameters()).example())


def native_func(parameters, args, kws):
    '''This function takes parameters, given as OrderedDicts generated by
    parameters(), builds a string representing a valid Python 3
    function, and then uses exec to compile the string and return the
    generated function.  If nonemptry strings are passed to args
    and/or, the generated function will have varargs and/or varkws.

    Args:
      parameters: OrderedDicts of parameter names and defaults, as a two-tuple.
      args: A string to name the varargs, if any.
      kws: A string to name the varkws, if any.

    Returns:
      A native Python 3 function with appropriate arguments.

    '''
    positional_or_kw, kw_only = parameters
    code = []
    return_code = ', '.join(
        itertools.chain(reversed(positional_or_kw), reversed(kw_only)))
    for name in reversed(positional_or_kw):
        default = positional_or_kw[name]
        if default is not no_default:
            code.append('%s=%s' % (name, default))
        else:
            code.append(name)
    if args:
        code.append('*args')
        if return_code:
            return_code += ', args'
        else:
            return_code += 'args'
    elif kw_only:
        code.append('*')
    for name in reversed(kw_only):
        default = kw_only[name]
        if default is not no_default:
            code.append('%s=%s' % (name, default))
        else:
            code.append(name)
    if kws:
        code.append('**kws')
        if return_code:
            return_code += ', kws'
        else:
            return_code += 'kws'
    namespace = {}
    print('def f(%s): return %s' % (', '.join(code), return_code))
    exec('def f(%s): return %s' % (', '.join(code), return_code), namespace)
    return namespace['f']

# print(inspect.getfullargspec(strategy(strategies.builds(native_func, parameters(), strategies.booleans(), strategies.booleans())).example()))


def decorated_func(parameters, args, kws):
    '''This function takes parameters, given as OrderedDicts generated by
    parameters(), builds a string representing a valid Python 3
    function containing all the argument names as positional-or-keword
    parameters, compiles it with exec, decorates it with the
    keyword_only_args decorator to make some arguments keyword-only,
    and then returns the decorated function.  If nonemptry strings are
    passed to args and/or, the generated function will have varargs
    and/or varkws.

    Args:
      parameters: OrderedDicts of parameter names and defaults, as a two-tuple.
      args: A string to name the varargs, if any.
      kws: A string to name the varkws, if any.

    Returns:
      A decorated function with appropriate arguments.

    '''
    
    positional_or_kw, kw_only = parameters
    defaults = []
    no_defaults = []
    return_code = ', '.join(
        itertools.chain(reversed(positional_or_kw), reversed(kw_only)))
    for name in itertools.chain(reversed(positional_or_kw), reversed(kw_only)):
        try:
            default = positional_or_kw[name]
        except KeyError:
            default = kw_only[name]
        if default is not no_default:
            defaults.append('%s=%s' % (name, default))
        else:
            no_defaults.append(name)
    code = no_defaults + defaults
    if args:
        code.append('*args')
        if return_code:
            return_code += ', args'
        else:
            return_code += 'args'
    if kws:
        code.append('**kws')
        if return_code:
            return_code += ', kws'
        else:
            return_code += 'kws'
    namespace = {}
    exec('def f(%s): return %s' % (', '.join(code), return_code), namespace)
    return keyword_only_args(*kw_only)(namespace['f'])

# print(inspect.getfullargspec(strategy(strategies.builds(decorated_func, parameters(), strategies.booleans(), strategies.booleans())).example().__wrapped__))


@strategies.composite
def generate_parameters(draw):
    '''This is a Hypothesis strategy to generate appropriate parameters to
    use to make a native and a decorated function for comparison and
    then generates arguments to call those two functions with,
    including extra positional and keyword arguments if necessary.  It
    uses parameters() to generate the parameter names and defaults.

    '''
    positional_or_kw, kw_only = draw(parameters())
    # print(positional_or_kw, kw_only)
    varargs = draw(strategies.booleans())
    varkw = draw(strategies.booleans())
    if kw_only:
        kws = draw(strategies.dictionaries(
            keys=strategies.sampled_from(kw_only),
            values=strategies.text(min_size=1),
            average_size=len(kw_only)))
    else:
        kws = {}
    if positional_or_kw:
        kws.update(draw(strategies.dictionaries(
            keys=strategies.sampled_from(positional_or_kw),
            values=strategies.text(min_size=1))))
    args = draw(strategies.lists(
        strategies.text(min_size=1),
        average_size=max(1, len(positional_or_kw) + len(kw_only) - len(kws))))
    return args, kws, positional_or_kw, kw_only, varargs, varkw

@hypothesis.given(generate_parameters())
def test(parameters):
    '''This Hypothesis test integrates everything, calling
    generate_parameters() to get arguments and parameters, using
    native_func() and decorated_func() to make the functions, and then
    calling the functions with the arguments to check if they have the
    same output. '''

    args, kws, positional_or_kw, kw_only, varargs, varkw = parameters
    native = native_func((positional_or_kw, kw_only), varargs, varkw)
    decorated = decorated_func((positional_or_kw, kw_only), varargs, varkw)
    try:
        print(native(*args, **kws))
        print(decorated(*args, **kws))
        assert native(*args, **kws) == decorated(*args, **kws)
    except TypeError as native_type_error:
        try:
            decorated(*args, **kws)
        except TypeError as decorated_type_error:
            pass
            # assert native_type_error.args[0] == decorated_type_error.args[0]

if __name__ == '__main__':
    test()
