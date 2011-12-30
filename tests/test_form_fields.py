# -*- coding: utf-8 -*-

import unittest

from wiseguy import form_fields

class TestInput(unittest.TestCase):
    def test_plain(self):
        context = dict(data=None, errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="text" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_empty(self):
        context = dict()
        expected = '''
<label for="foo">Foo:</label>
<input type="text" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_compulsory(self):
        context = dict()
        expected = '''
<label for="foo">Foo:*</label>
<input type="text" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:", compulsory=True)
        assert expected == result

    def test_data(self):
        context = dict(data=dict(foo='blah'), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="text" id="foo" value="blah" name="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_errors(self):
        context = dict(data=dict(), errors=dict(foo="Please enter a foo"))
        expected = '''
<label for="foo">Foo:</label>
<input type="text" id="foo" value="" name="foo">
<span class="error">Please enter a foo</span>
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_non_ascii(self):
        context = dict(data=dict(foo=u'blah£'), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="text" id="foo" value="blah&#163;" name="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result

    def test_non_text(self):
        context = dict(data=dict(foo=1), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="text" id="foo" value="1" name="foo">
        '''.strip()
        result = form_fields.input(context, 'foo', "Foo:")
        assert expected == result


class TestCheckbox(unittest.TestCase):
    def test_plain(self):
        context = dict(data=None, errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="checkbox" id="foo" value="" name="foo">
'''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:")
        assert expected == result

    def test_with_value(self):
        context = dict(data=None, errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="checkbox" id="foo" value="wibble" name="foo">
'''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:", value="wibble")
        assert expected == result

    def test_empty(self):
        context = dict()
        expected = '''
<label for="foo">Foo:</label>
<input type="checkbox" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:")
        assert expected == result

    def test_compulsory(self):
        context = dict()
        expected = '''
<label for="foo">Foo:*</label>
<input type="checkbox" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:", compulsory=True)
        assert expected == result

    def test_data(self):
        context = dict(data=dict(foo=['blah', 'wangle']), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="checkbox" id="foo" value="blah" name="foo" checked>
        '''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:", value="blah")
        assert expected == result

    def test_errors(self):
        context = dict(data=dict(), errors=dict(foo="Please enter a foo"))
        expected = '''
<label for="foo">Foo:</label>
<input type="checkbox" id="foo" value="" name="foo">
<span class="error">Please enter a foo</span>
        '''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:")
        assert expected == result

    def test_disabled(self):
        context = dict()
        expected = '''
<label for="foo">Foo:</label>
<input type="checkbox" id="foo" value="" name="foo" disabled>
        '''.strip()
        result = form_fields.checkbox(context, 'foo', "Foo:", disabled=True)
        assert expected == result


class TestPassword(unittest.TestCase):
    def test_plain(self):
        context = dict(data=None, errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="password" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.password(context, 'foo', "Foo:")
        assert expected == result

    def test_empty(self):
        context = dict()
        expected = '''
<label for="foo">Foo:</label>
<input type="password" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.password(context, 'foo', "Foo:")
        assert expected == result

    def test_compulsory(self):
        context = dict()
        expected = '''
<label for="foo">Foo:*</label>
<input type="password" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.password(context, 'foo', "Foo:", compulsory=True)
        assert expected == result

    def test_data(self):
        context = dict(data=dict(foo='blah'), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<input type="password" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.password(context, 'foo', "Foo:")
        assert expected == result

    def test_errors(self):
        context = dict(data=dict(), errors=dict(foo="Please enter a foo"))
        expected = '''
<label for="foo">Foo:</label>
<input type="password" id="foo" value="" name="foo">
<span class="error">Please enter a foo</span>
        '''.strip()
        result = form_fields.password(context, 'foo', "Foo:")
        assert expected == result


class TestSelect(unittest.TestCase):
    def test_plain(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        expected = '''
<label for="foo">Foo:</label>

<select id="foo" name="foo">
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>
        '''.strip()
        result = form_fields.select({}, 'foo', "Foo:", options)
        result = result.strip()
        assert expected == result

    def test_compulsory(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        expected = '''
<label for="foo">Foo:*</label>

<select id="foo" name="foo">
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>
        '''.strip()
        result = form_fields.select({}, 'foo', "Foo:", options, compulsory=True)
        result = result.strip()
        assert expected == result

    def test_data(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        context = dict(data=dict(foo='bar3'))
        expected = '''
<label for="foo">Foo:</label>

<select id="foo" name="foo">
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option selected value="bar3">Bar 3</option></select>
        '''.strip()
        result = form_fields.select(context, 'foo', "Foo:", options)
        result = result.strip()
        assert expected == result

    def test_errors(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        context = dict(errors=dict(foo='Please choose a foo'))
        expected = '''
<label for="foo">Foo:</label>

<select id="foo" name="foo">
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>

<span class="error">Please choose a foo</span>
        '''.strip()
        result = form_fields.select(context, 'foo', "Foo:", options)
        result = result.strip()
        assert expected == result

    def test_with_values(self):
        options = ["one", "two", "three"]
        context = dict()
        expected = '''
<label for="foo">Foo:</label>

<select id="foo" name="foo">
<option value=""></option>
<option value="one">one</option>
<option value="two">two</option>
<option value="three">three</option></select>
        '''.strip()
        result = form_fields.select(context, 'foo', "Foo:", options)
        result = result.strip()
        assert expected == result

    def test_disabled(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        context = dict()
        expected = '''<label for="foo">Foo:</label>

<select id="foo" name="foo" disabled>
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>
'''
        result = form_fields.select(context, 'foo', "Foo:", options, disabled=True)
        assert expected == result

    def test_without_blank_option(self):
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        context = dict()
        expected = '''<label for="foo">Foo:</label>

<select id="foo" name="foo">
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select>
'''
        result = form_fields.select(context, 'foo', "Foo:", options, blank_option=False)
        assert expected == result


class TestDatePicker(unittest.TestCase):
    def test_simple(self):
        context = dict()
        expected = '''
<script>$(function() {$("#foo").datepicker({dateFormat:'yy-mm-dd'});});</script>
<label for="foo">Foo:</label>
<input type="text" id="foo" value="" name="foo">
        '''.strip()
        result = form_fields.datepicker(context, 'foo', "Foo:")
        result = result.strip()
        assert expected == result


class TestTextArea(unittest.TestCase):
    def test_plain(self):
        context = dict(data=None, errors=None)
        expected = '''
<label for="foo">Foo:</label>
<textarea id="foo" rows="4" cols="40" name="foo"></textarea>
        '''.strip()
        result = form_fields.textarea(context, 'foo', "Foo:")
        assert expected == result

    def test_empty(self):
        context = dict()
        expected = '''
<label for="foo">Foo:</label>
<textarea id="foo" rows="4" cols="40" name="foo"></textarea>
        '''.strip()
        result = form_fields.textarea(context, 'foo', "Foo:")
        assert expected == result

    def test_compulsory(self):
        context = dict()
        expected = '''
<label for="foo">Foo:*</label>
<textarea id="foo" rows="4" cols="40" name="foo"></textarea>
        '''.strip()
        result = form_fields.textarea(context, 'foo', "Foo:", compulsory=True)
        assert expected == result

    def test_data(self):
        context = dict(data=dict(foo='Flibble Giblets'), errors=None)
        expected = '''
<label for="foo">Foo:</label>
<textarea id="foo" rows="4" cols="40" name="foo">Flibble Giblets</textarea>
        '''.strip()
        result = form_fields.textarea(context, 'foo', "Foo:")
        assert expected == result

    def test_errors(self):
        context = dict(data=dict(), errors=dict(foo="Please enter a foo"))
        expected = '''
<label for="foo">Foo:</label>
<textarea id="foo" rows="4" cols="40" name="foo"></textarea>
<span class="error">Please enter a foo</span>
        '''.strip()
        result = form_fields.textarea(context, 'foo', "Foo:")
        assert expected == result


class TestTinyMCE(unittest.TestCase):
    def test_simple(self):
        context = dict(data=None, errors=None)
        expected = '''
<script type="text/javascript">
tinyMCE.init({
mode : "textareas",
theme : "simple",
editor_selector : "mceEditor",
editor_deselector : "mceNoEditor"
});
</script>
<label for="foo">Foo:*</label>
<textarea id="foo" rows="4" cols="40" name="foo" class="mceEditor"></textarea>
        '''.strip()
        result = form_fields.tinymce(context, 'foo', "Foo:", compulsory=True)
        assert expected == result


class TestSubmit(unittest.TestCase):
    def test_plain(self):
        expected = '''<input type="submit" id="submit" value="Submit">'''
        result = form_fields.submit()
        result = result.strip()
        assert expected == result

    def test_with_labels(self):
        expected = '''<input type="submit" id="foo" value="Foo!">'''
        result = form_fields.submit('foo', "Foo!")
        result = result.strip()
        assert expected == result

    def test_bad_value(self):
        expected = '''<input type="submit" id="foo" value="Foo&amp;&lt;">'''
        result = form_fields.submit('foo', "Foo&<")
        result = result.strip()
        assert expected == result

    def test_with_classes(self):
        expected = '''<input type="submit" id="submit" value="Submit" class="foo bar">'''
        result = form_fields.submit(class_="foo bar")
        result = result.strip()
        assert expected == result


class TestBootstrapFormFields(unittest.TestCase):
    def test_input(self):
        context = dict(data=None, errors=None)
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:</label><div class="controls"><input type="text" id="foo" value="" name="foo"></div>
</fieldset>'''.strip()
        result = form_fields.bootstrap_input(context, 'foo', "Foo:")
        result = result.strip()
        assert expected == result

    def test_password(self):
        context = dict(data=None, errors=None)
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:</label><div class="controls"><input type="password" id="foo" value="" name="foo"></div>
</fieldset>'''.strip()
        result = form_fields.bootstrap_password(context, 'foo', "Foo:")
        result = result.strip()
        assert expected == result

    def test_select(self):
        context = dict(data=None, errors=None)
        options = [('bar1', "Bar 1"), ('bar2', "Bar 2"), ('bar3', "Bar 3")]
        expected = '''
<fieldset class="control-group">
<label for="foo" class="control-label">Foo:</label><div class="controls"><select id="foo" name="foo">
<option value=""></option>
<option value="bar1">Bar 1</option>
<option value="bar2">Bar 2</option>
<option value="bar3">Bar 3</option></select></div>
</fieldset>'''.strip()
        result = form_fields.bootstrap_select({}, 'foo', "Foo:", options)
        result = result.strip()
        assert expected == result
