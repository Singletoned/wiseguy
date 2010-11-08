# -*- coding: utf-8 -*-

import jinja2 as j2
import werkzeug as wz

html = wz.HTMLBuilder('html')


def add_errors(context, elements, id):
    "Add an error, if present, to the list of elements"
    if context.get('errors', None):
        if context['errors'].get(id, ''):
            elements.append(
                html.span(
                    context['errors'][id],
                    class_='error'))


@j2.contextfunction
def input(context, id, label, compulsory=False):
    if compulsory:
        label = label + "*"
    elements = [
        html.label(
            label,
            for_=id),
        html.input(
            type="text",
            name=id,
            id=id,
            value=j2.escape((context.get('data', False) or {}).get(id, '')))]
    add_errors(context, elements, id)
    return '\n'.join(elements)


@j2.contextfunction
def password(context, id, label, compulsory=False):
    if compulsory:
        label = label + "*"
    elements = [
        html.label(
            label,
            for_=id),
        html.input(
            type="password",
            name=id,
            id=id,
            value="")]
    add_errors(context, elements, id)
    return '\n'.join(elements)


def select(context, id, label, options, compulsory=False):
    if compulsory:
        label = label + "*"
    option_elements = []
    selected = (context.get('data', False) or {}).get(id, '')
    for (value, text) in options:
        if value == selected:
            o = html.option(text, value=value, selected=True)
        else:
            o = html.option(text, value=value)
        option_elements.append("  %s\n"%o)
    elements = [
        html.label(
            label,
            for_=id),
        html.select(
            "\n",
            *option_elements,
            name=id,
            id=id)]
    add_errors(context, elements, id)
    return '\n'.join(elements)


def submit(id="submit", label="Submit"):
    element = html.input(
        type="submit",
        id=id,
        value=label)
    return element
