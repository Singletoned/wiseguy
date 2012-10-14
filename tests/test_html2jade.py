# -*- coding: utf-8 -*-

from wiseguy import html2jade


def test_simple():
    html = '''<p>Hello</p>'''
    expected = '''p Hello'''
    result = html2jade.html2jade(html)
    assert result == expected
