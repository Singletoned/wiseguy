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
