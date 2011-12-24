# -*- coding: utf-8 -*-

import jinja2 as j2
import werkzeug as wz
import lxml.html
from lxml.html import builder as html


def add_errors(context, elements, id):
    "Add an error, if present, to the list of elements"
    if context.get('errors', None):
        if context['errors'].get(id, ''):
            elements.append(
                html.SPAN(
                    context['errors'][id],
                    {'class': 'error'}))


def _input(context, id, label, compulsory):
    if compulsory:
        label = label + "*"
    elements = [
        html.LABEL(
            label,
            {'for': id}),
        html.INPUT(
            type="text",
            name=id,
            id=id,
            value=str((context.get('data', False) or {}).get(id, '')))]
    add_errors(context, elements, id)
    return elements


@j2.contextfunction
def input(context, id, label, compulsory=False):
    "A simple input element"
    elements = _input(context, id, label, compulsory)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


@j2.contextfunction
def bootstrap_input(context, id, label, compulsory=False):
    "A Bootstrap input element"
    elements = _input(context, id, label, compulsory=False)
    label, input = elements
    label.attrib['class'] = "control-label"
    input = html.DIV(
        input,
        {'class': 'controls'})
    element = html.FIELDSET(
        label,
        input,
        {'class': 'control-group'})
    element = lxml.html.tostring(element, pretty_print=True)
    return element


@j2.contextfunction
def password(context, id, label, compulsory=False):
    "A password element.  Won't fill the value even if present in context['data']"
    if compulsory:
        label = label + "*"
    elements = [
        html.LABEL(
            label,
            {'for': id}),
        html.INPUT(
            type="password",
            name=id,
            id=id,
            value="")]
    add_errors(context, elements, id)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def select(context, id, label, options, compulsory=False):
    "A select element.  Accepts a list of value, text pairs"
    if compulsory:
        label = label + "*"
    option_elements = []
    selected = (context.get('data', False) or {}).get(id, '')
    for (value, text) in options:
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
