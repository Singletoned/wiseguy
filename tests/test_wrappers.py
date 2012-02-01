# -*- coding: utf-8 -*-

from lxml.html import builder as html

from wiseguy import wrappers

def test_add_class():
    d = html.DIV()
    wrappers.add_class(d, 'foo')
    assert d.attrib['class'] == 'foo'
