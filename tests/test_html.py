# -*- coding: utf-8 -*-

import pyjade

import wiseguy as wg
import wiseguy.html


def test_process_jade():
    "Test that Jade basically works"
    d = "div#foo.bar Hullo"
    expected = '''
<div id="foo" class="bar">Hullo
</div>'''
    result = wg.html.process_jade(d)
    assert expected == result
