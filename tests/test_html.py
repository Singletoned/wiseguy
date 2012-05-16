# -*- coding: utf-8 -*-

import pyjade

import wiseguy as wg
import wiseguy.html


def test_process_jade():
    "Test that Jade basically works"
    d = "div#foo.bar Hullo"
    expected = '''<div id="foo" class="bar">Hullo</div>'''
    result = wg.html.process_jade(d)
    assert expected == result

def test_jade():
    d = wg.html.jade("html: body: div#main")
    assert d.tag == "html"

    expected = '''<html><body><div id="main">    </div>  </body></html>'''
    result = d.to_string()
    assert result == expected
