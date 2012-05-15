# -*- coding: utf-8 -*-

import pyjade

from wiseguy.html import process_jade


def test_process_jade():
    "Test that Jade basically works"
    d = "div#foo.bar Hullo"
    expected = '''
<div id="foo" class="bar">Hullo
</div>'''
    result = process_jade(d)
    assert expected == result
