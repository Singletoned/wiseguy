# -*- coding: utf-8 -*-

import werkzeug as wz

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


def test_create_expose():
    url_map = wz.routing.Map()
    expose = utils.create_expose(url_map)

    @expose("/index")
    def index():
        return "index"

    assert len(url_map._rules) == 1
    r = url_map._rules[0]
    assert r.endpoint == index


def test_mock_object():
    m1 = utils.MockObject(foo=1, bar='flam')
    assert m1.foo == 1
    assert m1.bar == 'flam'
    m2 = utils.MockObject(foo=1, bar='flam')
    assert m1 == m2
    assert repr(m1) == "<MockObject foo=1, bar='flam'>"
