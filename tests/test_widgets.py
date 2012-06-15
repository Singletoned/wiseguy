# -*- coding: utf-8 -*-

import unittest

import lxml.html
import werkzeug as wz

from wiseguy import widgets

url = wz.Href('/')
item_url = wz.Href('/item_type')


class TestPagination(unittest.TestCase):
    kwargs_filter = staticmethod(lambda c, **k: dict(offset=k['offset']))

    def test_prev_li_disabled(self):
        context = dict(offset=0, limit=5)
        expected = '''
<li class="prev disabled"><a>&#8592; Previous</a></li>
        '''.strip()
        result = widgets.prev_li(context, item_url)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_prev_li_enabled(self):
        context = dict(offset=1, limit=5)
        expected = '''
<li class="prev"><a href="/item_type?limit=5&amp;offset=0">&#8592; Previous</a></li>
        '''.strip()
        result = widgets.prev_li(context, item_url)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_prev_li_with_kwargs_filter(self):
        context = dict(offset=1, limit=5, DEFAULT_LIMIT=5)
        expected = '''
<li class="prev"><a href="/item_type?offset=0">&#8592; Previous</a></li>
        '''.strip()
        result = widgets.prev_li(context, item_url, self.kwargs_filter)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_next_li_disabled(self):
        context = dict(offset=0, limit=5, total=5)
        expected = '''
<li class="next disabled"><a>Next &#8594;</a></li>
        '''.strip()
        result = widgets.next_li(context, item_url)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_next_li_enabled(self):
        context = dict(offset=0, limit=5, total=10)
        expected = '''
<li class="next"><a href="/item_type?limit=5&amp;offset=5">Next &#8594;</a></li>
        '''.strip()
        result = widgets.next_li(context, item_url)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_next_li_with_kwargs_filter(self):
        context = dict(offset=0, limit=5, total=10, DEFAULT_LIMIT=5)
        expected = '''
<li class="next"><a href="/item_type?offset=5">Next &#8594;</a></li>
        '''.strip()
        result = widgets.next_li(context, item_url, self.kwargs_filter)
        result = lxml.html.tostring(result)
        assert expected == result

    def test_simple(self):
        context = dict(offset=0, total=25, limit=5, url=url)
        expected = '''
<div class="pagination"><ul>
<li class="prev disabled"><a>&#8592; Previous</a></li>
<li class="active"><a href="/item_type?limit=5&amp;offset=0">1</a></li>
<li><a href="/item_type?limit=5&amp;offset=5">2</a></li>
<li><a href="/item_type?limit=5&amp;offset=10">3</a></li>
<li><a href="/item_type?limit=5&amp;offset=15">4</a></li>
<li><a href="/item_type?limit=5&amp;offset=20">5</a></li>
<li class="next"><a href="/item_type?limit=5&amp;offset=5">Next &#8594;</a></li>
</ul></div>
'''.strip()
        result = widgets.pagination(context, item_url).strip()
        assert expected == result

    def test_with_class(self):
        context = dict(offset=0, total=25, limit=5, url=url)
        expected = '''
<div class="pagination centered"><ul>
<li class="prev disabled"><a>&#8592; Previous</a></li>
<li class="active"><a href="/item_type?limit=5&amp;offset=0">1</a></li>
<li><a href="/item_type?limit=5&amp;offset=5">2</a></li>
<li><a href="/item_type?limit=5&amp;offset=10">3</a></li>
<li><a href="/item_type?limit=5&amp;offset=15">4</a></li>
<li><a href="/item_type?limit=5&amp;offset=20">5</a></li>
<li class="next"><a href="/item_type?limit=5&amp;offset=5">Next &#8594;</a></li>
</ul></div>
'''.strip()
        result = widgets.pagination(context, item_url, class_="centered").strip()
        assert expected == result

    def test_with_kwargs_filter(self):
        context = dict(offset=10, total=25, limit=5, url=url, DEFAULT_LIMIT=5)
        expected = '''
<div class="pagination"><ul>
<li class="prev"><a href="/item_type?offset=5">&#8592; Previous</a></li>
<li><a href="/item_type?offset=0">1</a></li>
<li><a href="/item_type?offset=5">2</a></li>
<li class="active"><a href="/item_type?offset=10">3</a></li>
<li><a href="/item_type?offset=15">4</a></li>
<li><a href="/item_type?offset=20">5</a></li>
<li class="next"><a href="/item_type?offset=15">Next &#8594;</a></li>
</ul></div>
'''.strip()
        result = widgets.pagination(context, item_url, self.kwargs_filter).strip()
        assert expected == result


class TestPagecounter(unittest.TestCase):
    def test_simple(self):
        context = dict(offset=0, total=25, limit=5)
        page_counter = widgets.page_counter(context)
        result = list(page_counter)
        expected = [
            dict(page=1, offset=0,  limit=5, start=1,  end=5,  active=True),
            dict(page=2, offset=5,  limit=5, start=6,  end=10, active=False),
            dict(page=3, offset=10, limit=5, start=11, end=15, active=False),
            dict(page=4, offset=15, limit=5, start=16, end=20, active=False),
            dict(page=5, offset=20, limit=5, start=21, end=25, active=False),
        ]
        assert expected == result


class TestBreadcrumbs(unittest.TestCase):
    def test_simple(self):
        expected = '''
<ul class="breadcrumb"><li class="active"><a href="/">My Site</a></li></ul>
        '''.strip()
        pages = [("/", "My Site")]
        result = widgets.breadcrumbs(pages).strip()
        assert expected == result

    def test_two_levels(self):
        expected = '''
<ul class="breadcrumb">
<li>
<a href="/">My Site</a> <span class="divider">/</span>
</li>
<li class="active"><a href="/foo">Foo</a></li>
</ul>
        '''.strip()
        pages = [("/", "My Site"), ("/foo", "Foo")]
        result = widgets.breadcrumbs(pages).strip()
        assert expected == result
