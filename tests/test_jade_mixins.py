# -*- coding: utf-8 -*-

import unittest

import wiseguy.jade_mixins


class TestSelect(unittest.TestCase):
    def test_plain(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        expected = '''
<select id="foo" name="foo"><option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>
        '''.strip()
        result = wiseguy.jade_mixins.select('foo', options).strip()
        self.assertEqual(expected, result)

    def test_with_values(self):
        options = ["one", "two", "three"]
        context = dict()
        expected = '''
<select id="foo" name="foo"><option value="one">one</option>
<option value="two">two</option>
<option value="three">three</option></select>
        '''.strip()
        result = wiseguy.jade_mixins.select('foo', options).strip()
        self.assertEqual(expected, result)

    def test_with_blank_option(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        context = dict()
        expected = '''
<select id="foo" name="foo"><option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>
'''.strip()
        result = wiseguy.jade_mixins.select('foo', options, blank_option=True).strip()
        self.assertEqual(expected, result)
