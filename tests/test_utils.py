# -*- coding: utf-8 -*-

from wiseguy import utils

def test_decamelise():
    pairs = [
        ("CamelCase", 'camel_case'),
        ("HTTPServer", 'http_server'),
        (u"CamelCase", u'camel_case'),
        (u"HTTPServer", u'http_server'),
    ]

    for data, expected in pairs:
        assert utils.decamelise(data) == expected
        assert type(expected) == type(data)
