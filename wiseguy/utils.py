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
