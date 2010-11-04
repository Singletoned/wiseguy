# -*- coding: utf-8 -*-

import re


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
