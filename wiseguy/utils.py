# -*- coding: utf-8 -*-

import re

from werkzeug.routing import Rule


def create_expose(url_map):
    def expose(rule, methods=['GET'], **kw):
        def decorate(f):
            kw['endpoint'] = f
            url_map.add(Rule(rule, methods=methods, **kw))
            return f
        return decorate
    return expose


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
