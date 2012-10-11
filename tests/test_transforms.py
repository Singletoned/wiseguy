# -*- coding: utf-8 -*-

import wiseguy.transforms
import wiseguy.html

def test_add_stylesheet():
    transform = wiseguy.transforms.add_stylesheet("foo.css")
    element = wiseguy.html.jade("html: head")

    assert transform.keys == set(['url'])
    transform.action(
        element=element,
        url=lambda x: "url:%s"%x)
    result = element.to_string().strip()
    expected = """
<html><head><link href="url:foo.css" type="text/css" rel="stylesheet"></head></html>
    """.strip()
    assert result == expected


def test_add_script():
    transform = wiseguy.transforms.add_script("foo.js")
    element = wiseguy.html.jade("html: head")

    assert transform.keys == set(['url'])
    transform.action(
        element=element,
        url=lambda x: "url:%s"%x)
    result = element.to_string().strip()
    expected = """
<html><head><script src="url:foo.js"></script></head></html>
    """.strip()
    assert result == expected
