# -*- coding: utf-8 -*-

import unittest

import lxml.html
from lxml.html import builder as html

from wiseguy import form_fields, wrappers


def test_add_class():
    d = html.DIV()
    wrappers._add_class(d, 'foo')
    assert d.attrib['class'] == 'foo'


def test_replace():
    tree = lxml.html.fromstring(
'''
<div>
  <span class="foo">Hello World</span>
  <span>!</span>
</div>''')
    path = "//span[@class='foo']"
    new_element = lxml.html.fromstring('''<b>Foo</b>''')
    expected = '''
<div>
  <b>Foo</b><span>!</span>
</div>'''.strip()
    result = lxml.html.tostring(
        wrappers.replace(tree, path, new_element)).strip()
    assert expected == result

class TestWrappers(unittest.TestCase):
    bootstrap_form_fields = form_fields.BootstrapFormFields()

    def test_width_select(self):
        context = dict(data=None, errors=None)
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:</label><div class="controls"><select id="foo" name="foo" class="span5">
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select></div>
</fieldset>'''.strip()
        result = wrappers.width(
            self.bootstrap_form_fields.select({}, 'foo', "Foo:", options),
            5)
        result = lxml.html.tostring(result, pretty_print=True).strip()
        assert expected == result

    def test_width_input(self):
        context = dict(data=None, errors=None)
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:</label><div class="controls"><input type="text" id="foo" value="" name="foo" class="span5"></div>
</fieldset>'''.strip()
        result = wrappers.width(
            self.bootstrap_form_fields.input(context, 'foo', "Foo:"),
            5)
        result = lxml.html.tostring(result, pretty_print=True).strip()
        assert expected == result

    def test_compulsory(self):
        context = dict()
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:*</label><div class="controls"><input type="text" id="foo" value="" name="foo"></div>
</fieldset>'''.strip()
        result = wrappers.compulsory(
            self.bootstrap_form_fields.input(context, 'foo', "Foo:"))
        result = lxml.html.tostring(result, pretty_print=True).strip()
        assert expected == result

    def test_with_class(self):
        context = dict()
        expected = '''
<fieldset class="control-group flamble">
<label for="foo" class="control-label">Foo:</label><div class="controls"><input type="text" id="foo" value="" name="foo"></div>
</fieldset>'''.strip()
        result = wrappers.with_class(
            self.bootstrap_form_fields.input(context, 'foo', "Foo:"),
            "//fieldset",
            "flamble")
        result = lxml.html.tostring(result, pretty_print=True).strip()
        assert expected == result
