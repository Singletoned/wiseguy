# -*- coding: utf-8 -*-

from wiseguy import html2jade


data = (
    (
        '''<p>Hello</p>''',
        '''p Hello'''),
    (
        '''<div><p>Hello</p><p>World</p></div>''',
        '''
div
  p Hello
  p World'''.strip()),
)

def test_simple():
    for (html, expected) in data:
        result = html2jade.html2jade(html)
        assert result == expected
