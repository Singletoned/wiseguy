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
