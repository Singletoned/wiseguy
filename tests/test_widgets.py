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

    def test_simple(self):
        context = dict(offset=0, total=25, limit=5)
        expected = '''
<div class="pagination"><ul>
<li class="prev disabled"><a href="#">&#8592; Previous</a></li>
<li class="active"><a href="#">1</a></li>
<li><a href="#">2</a></li>
<li><a href="#">3</a></li>
<li><a href="#">4</a></li>
<li><a href="#">5</a></li>
<li class="next"><a href="#">Next &#8594;</a></li>
</ul></div>
'''.strip()
        result = widgets.pagination(context).strip()
        assert expected == result


class TestPagecounter(unittest.TestCase):
    def test_simple(self):
        context = dict(offset=0, total=25, limit=5)
        page_counter = widgets.page_counter(context)
        result = list(page_counter)
        expected = [
            dict(page=1, start=1,  end=5,  active=True),
            dict(page=2, start=6,  end=10, active=False),
            dict(page=3, start=11, end=15, active=False),
            dict(page=4, start=16, end=20, active=False),
            dict(page=5, start=21, end=25, active=False),
        ]
        assert expected == result
