# -*- coding: utf-8 -*-

import unittest

import lxml.html

from wiseguy import widgets


class TestPagination(unittest.TestCase):
    def test_prev_li_disabled(self):
        context = dict(offset=0)
        expected = '''
<li class="prev disabled"><a href="#">&#8592; Previous</a></li>
        '''.strip()
        result = widgets.prev_li(context)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_prev_li_enabled(self):
        context = dict(offset=1)
        expected = '''
<li class="prev"><a href="#">&#8592; Previous</a></li>
        '''.strip()
        result = widgets.prev_li(context)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_next_li_disabled(self):
        context = dict(offset=0, limit=5, total=5)
        expected = '''
<li class="next disabled"><a href="#">Next &#8594;</a></li>
        '''.strip()
        result = widgets.next_li(context)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_next_li_enabled(self):
        context = dict(offset=0, limit=5, total=10)
        expected = '''
<li class="next"><a href="#">Next &#8594;</a></li>
        '''.strip()
        result = widgets.next_li(context)
        result = lxml.html.tostring(result)
        assert expected == result
