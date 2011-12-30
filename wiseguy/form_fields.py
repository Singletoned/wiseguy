# -*- coding: utf-8 -*-

import jinja2 as j2
import werkzeug as wz
import lxml.html
from lxml.html import builder as html

_default = object()

def add_errors(context, elements, id):
    "Add an error, if present, to the list of elements"
    if context.get('errors', None):
        if context['errors'].get(id, ''):
            elements.append(
                html.SPAN(
                    context['errors'][id],
                    {'class': 'error'}))


def _boostrapise(func, *args, **kwargs):
    elements = func(*args, **kwargs)
    label = elements[0]
    input = elements[1]
    rest = elements[2:]
    label.attrib['class'] = "control-label"
    input = html.DIV(
        input,
        {'class': 'controls'})
    element = html.FIELDSET(
        label,
        input,
        {'class': 'control-group'},
        *rest)
    element = lxml.html.tostring(element, pretty_print=True)
    return element


def _input(context, id, label, compulsory, input_type, value=_default):
    if value is _default:
        value = unicode((context.get('data', False) or {}).get(id, ''))
    if compulsory:
        label = label + "*"
    elements = [
        html.LABEL(
            label,
            {'for': id}),
        html.INPUT(
            type=input_type,
            name=id,
            id=id,
            value=value)]
    add_errors(context, elements, id)
    return elements


@j2.contextfunction
def input(context, id, label, compulsory=False):
    "A simple input element"
    elements = _input(context, id, label, compulsory, input_type="text")
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def _checkbox(context, id, label, compulsory=False, value=_default, disabled=False):
    elements = _input(context, id, label, compulsory, input_type="checkbox", value=value)
    data_value = (context.get('data', False) or {}).get(id, '')
    if isinstance(data_value, (list, tuple)):
        if value in data_value:
            elements[1].attrib['checked'] = "checked"
    if disabled:
        elements[1].attrib['disabled'] = "disabled"
    return elements


@j2.contextfunction
def checkbox(context, id, label, compulsory=False, value=_default, disabled=False):
    "A simple input element"
    elements = _checkbox(context, id, label, compulsory, value, disabled)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


@j2.contextfunction
def password(context, id, label, compulsory=False):
    "A password element.  Won't fill the value even if present in context['data']"
    elements = _input(context, id, label, compulsory, input_type="password")
    elements[1].attrib['value'] = ""
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def _datepicker(context, id, label, compulsory):
    elements = _input(context, id, label, compulsory, input_type="text")
    script = html.SCRIPT(
        '''$(function() {$("#%s").datepicker({dateFormat:'yy-mm-dd'});});''' % id)
    elements.insert(len(elements), script)
    return elements


@j2.contextfunction
def datepicker(context, id, label, compulsory=False):
    "A datepicker element that uses JQueryUI"
    elements = _datepicker(context, id, label, compulsory)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def _textarea(context, id, label, compulsory):
    if compulsory:
        label = label + "*"
    elements = [
        html.LABEL(
            label,
            {'for': id}),
        html.TEXTAREA(
            str((context.get('data', False) or {}).get(id, '')),
            name=id,
            id=id,
            rows="4",
            cols="40",
)]
    add_errors(context, elements, id)
    return elements


@j2.contextfunction
def textarea(context, id, label, compulsory=False):
    elements = _textarea(context, id, label, compulsory)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def _tinymce(context, id, label, compulsory):
    elements = _textarea(context, id, label, compulsory)
    elements[1].attrib['class'] = "mceEditor"
    script = html.SCRIPT(
        '''
tinyMCE.init({
mode : "textareas",
theme : "simple",
editor_selector : "mceEditor",
editor_deselector : "mceNoEditor"
});
''',
    type="text/javascript")
    elements.insert(len(elements), script)
    return elements


@j2.contextfunction
def tinymce(context, id, label, compulsory=False):
    elements = _tinymce(context, id, label, compulsory)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def _select(context, id, label, options, compulsory, disabled, blank_option):
    if compulsory:
        label = label + "*"
    option_elements = []
    selected = unicode((context.get('data', False) or {}).get(id, ''))
    if blank_option:
        o = html.OPTION(value="")
        option_elements.append(o)
    for option in options:
        if isinstance(option, (list, tuple)):
            value, text = option
        else:
            value, text = (option, option)
        value = unicode(value)
        text = unicode(text)
        if value == selected:
            o = html.OPTION(text, value=value, selected="selected")
        else:
            o = html.OPTION(text, value=value)
        option_elements.append(o)
    elements = [
        html.LABEL(
            label,
            {'for': id}),
        html.SELECT(
            "\n",
            *option_elements,
            name=id,
            id=id)]
    add_errors(context, elements, id)
    if disabled:
        elements[1].attrib['disabled'] = "disabled"
    return elements


@j2.contextfunction
def select(context, id, label, options, compulsory=False, disabled=False, blank_option=True):
    "A select element.  Accepts a list of value, text pairs"
    elements = _select(context, id, label, options, compulsory, disabled, blank_option)
    elements = [lxml.html.tostring(e, pretty_print=True) for e in elements]
    return '\n'.join(elements)


def submit(id="submit", label="Submit", class_=""):
    "A simple submit button"
    kwargs = dict(
        type="submit",
        id=id,
        value=label)
    if class_:
        args = ({'class': class_},)
    else:
        args = tuple()
    element = html.INPUT(
        *args,
        **kwargs)
    element = lxml.html.tostring(element, pretty_print=True)
    return element


class BootstrapFormFields(object):
    @j2.contextfunction
    def input(self, context, id, label, compulsory=False):
        "A Bootstrap input element"
        return _boostrapise(_input, context, id, label, compulsory=False, input_type="text")

    @j2.contextfunction
    def password(self, context, id, label, compulsory=False):
        "A Bootstrap input element"
        return _boostrapise(_input, context, id, label, compulsory, input_type="password")

    @j2.contextfunction
    def select(self, context, id, label, options, compulsory=False, disabled=False, blank_option=True):
        "A Bootstrap input element"
        return _boostrapise(_select, context, id, label, options, compulsory, disabled, blank_option)

    @j2.contextfunction
    def checkbox(self, context, id, label, compulsory=False, value=_default):
        "A Bootstrap checkbox element"
        return _boostrapise(_checkbox, context, id, label, compulsory, value=value)

    @j2.contextfunction
    def textarea(self, context, id, label, compulsory=False):
        "A Bootstrap textarea element"
        return _boostrapise(_textarea, context, id, label, compulsory)

    @j2.contextfunction
    def datepicker(self, context, id, label, compulsory=False):
        "A Bootstrap datepicker element"
        return _boostrapise(_datepicker, context, id, label, compulsory)

    @j2.contextfunction
    def tinymce(self, context, id, label, compulsory=False):
        "A Bootstrap tinymce element"
        return _boostrapise(_tinymce, context, id, label, compulsory)
