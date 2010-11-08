# -*- coding: utf-8 -*-

import unittest

from wiseguy import form_fields

class TestInput(unittest.TestCase):
    def test_plain(self):
        context = dict(data=None, errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="text" name="foo" value="" id="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_empty(self):
        context = dict()
        expected = '''
<label for="foo">Foo:</label>
<input type="text" name="foo" value="" id="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_compulsory(self):
        context = dict()
        expected = '''
<label for="foo">Foo:*</label>
<input type="text" name="foo" value="" id="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:", compulsory=True)
        assert expected == result

    def test_data(self):
        context = dict(data=dict(foo='blah'), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="text" name="foo" value="blah" id="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_errors(self):
        context = dict(data=dict(), errors=dict(foo="Please enter a foo"))
        expected = '''
<label for="foo">Foo:</label>
<input type="text" name="foo" value="" id="foo">
<span class="error">Please enter a foo</span>
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result
