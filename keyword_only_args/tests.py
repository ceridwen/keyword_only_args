import collections
import inspect
import itertools
import logging
import pprint
import string

import hypothesis
from hypothesis import strategy
from hypothesis import strategies

from keyword_only_args import decorator_factory as keyword_only_args, no_default


@strategies.composite
def parameters(draw):
    # I'm not testing the robustness of Python's argument handling, so
    # my primary concern is generating human-readable parameter names
    # that can't possibly be Python keywords.  Python has a limit of
    # 255 on the number of arguments to a function.
    positional_or_kw = draw(strategies.sets(strategies.text(
        alphabet=string.ascii_letters, min_size=1, max_size=3).map(
            lambda s: ''.join(s) + '_'), max_size=255))
    kw_only = draw(strategies.sets(strategies.text(
        alphabet=string.ascii_letters, min_size=1).map(
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
