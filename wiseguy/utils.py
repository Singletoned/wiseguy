# -*- coding: utf-8 -*-

import difflib, pprint, re, copy

import werkzeug as wz

_DEFAULT = object()

def flatten_dict(d):
    for k, v in d.items():
        if isinstance(v, list) and (len(v)==1):
            d[k] = v[0]
    return d

def listify(*args):
    """
    >>> l = [1, 2, 3, ]
    >>> listify('a', 'b', *l)
    ['a', 'b', 1, 2, 3]
    """
    return list(args)

def dotted_getattr(item, attr_string, default=_DEFAULT):
    """Breaks up ``attr_string`` by dots then recursively gets the elements from ``item``::
        >>> l = list()
        >>> dotted_getattr(l, u'append.__doc__')
        'L.append(object) -- append object to end'
    """
    attrs = attr_string.split(u'.')
    for attr in attrs:
        item = getattr(item, attr, _DEFAULT)
        if item is _DEFAULT:
            if default is _DEFAULT:
                # An AttributeError would have been raised, rereaise it now
                return getattr(item, attr)
            else:
                return default
    return item

def decamelise(s):
    """
    >>> decamelise("CamelCase")
    'camel_case'
    >>> decamelise("HTTPServer")
    'http_server'
    """
    s = re.sub(
        "([a-z])([A-Z])",
        lambda m: m.group(1) + "_" + m.group(2).lower(), s)
    s = re.sub(
        "([A-Z])([A-Z][a-z])",
        lambda m: m.group(1) + "_" + m.group(2).lower(), s)
    s = s.lower()
    return s

def join(joiner, iterable):
    iterable = iter(iterable)
    next_item = iterable.next()
    for queued_item in iterable:
        yield next_item
        yield copy.deepcopy(joiner)
        next_item = queued_item
    yield next_item


class MockObject(object):
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __repr__(self):
        attrs = ["%s=%s"%(k,repr(v)) for (k,v) in self.__dict__.items()]
        result = "<MockObject %s>" % ", ".join(attrs)
        return result

    def __eq__(self, other):
        d = [(k, v) for (k, v) in self.__dict__.items() if not k.startswith('__')]
        for key, value in d:
            if not getattr(other, key) == value:
                return False
        return True


def MockEnv(path, method, **kwargs):
    """Returns a simple WSGI environment.  Pretends to be a class.
    >>> env = MockEnv("/path", "POST")
    >>> env # doctest:+ELLIPSIS
    {'SERVER_PORT': '80', 'SERVER_PROTOCOL': 'HTTP/1.1', 'SCRIPT_NAME': '', 'wsgi.input': ...
    >>> env[u"PATH_INFO"]
    '/path'
    >>> env[u"REQUEST_METHOD"]
    'POST'
    """
    return wz.EnvironBuilder(path=path, method=method, **kwargs).get_environ()

def print_quick_pprint_diff(item1, item2):
    if not isinstance(item1, basestring):
        item1 = pprint.pformat(item1)
    if not isinstance(item2, basestring):
        item2 = pprint.pformat(item2)
    for line in list(difflib.unified_diff(item1.split('\n'), item2.split('\n'))):
        print line
