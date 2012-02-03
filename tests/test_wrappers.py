# -*- coding: utf-8 -*-

import unittest

import lxml.html
from lxml.html import builder as html

from wiseguy import form_fields, wrappers


def test_add_class():
    d = html.DIV()
    wrappers._add_class(d, 'foo')
    assert d.attrib['class'] == 'foo'


class TestWrappers(unittest.TestCase):
    bootstrap_form_fields = form_fields.BootstrapFormFields()

    def test_span5(self):
        context = dict(data=None, errors=None)
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:</label><div class="controls"><input type="text" id="foo" value="" name="foo" class="span5"></div>
</fieldset>'''.strip()
        result = wrappers.span(
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
