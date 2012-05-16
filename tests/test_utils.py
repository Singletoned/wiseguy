# -*- coding: utf-8 -*-

from wiseguy import utils


def test_flatten_dict():
    data = dict(
        empty=[],
        single=[1],
        multi=[1,2,3])
    result = utils.flatten_dict(data)
    expected = dict(
        empty=[],
        single=1,
        multi=[1,2,3])
    assert result == expected

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


def test_mock_object():
    m1 = utils.MockObject(foo=1, bar='flam')
    assert m1.foo == 1
    assert m1.bar == 'flam'
    m2 = utils.MockObject(foo=1, bar='flam')
    assert m1 == m2
    assert repr(m1) == "<MockObject foo=1, bar='flam'>"


def test_mock_env():
    env = utils.MockEnv("/path", "POST")
    assert env[u"PATH_INFO"] == '/path'
    assert env[u"REQUEST_METHOD"] == 'POST'

    env = utils.MockEnv("/path", "POST", headers=dict(Foo="flim flam"))
    assert env[u"HTTP_FOO"] == "flim flam"


def test_dotted_getattr():
    class Foo:
        class Bar:
            baz = 1

    result = utils.dotted_getattr(Foo, 'Bar.baz')
    expected = 1
    assert expected == result

    result = utils.dotted_getattr(Foo, 'Bum.botty', None)
    expected = None
    assert expected == result

    try:
        result = utils.dotted_getattr(Foo, 'Bar.botty')
    except AttributeError:
        pass
    else:
        raise
