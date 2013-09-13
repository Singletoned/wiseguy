# -*- coding: utf-8 -*-

import types

import pyjade.ext.html
import lxml.html, lxml.builder

import wiseguy.utils
import wiseguy.html_tidy


class HtmlElement(lxml.html.HtmlElement):
    def to_string(self, pretty=True, tidy=False):
        if tidy:
            return wiseguy.html_tidy.tidy_html(self)
        else:
            return lxml.html.tostring(self, pretty_print=pretty)

    def normalise(self):
        return wiseguy.html_tidy.normalise_html(self)

    def add(self, path, text_or_el, index=None):
        if path:
            elements = self.cssselect(path)
        else:
            elements = [self]
        if isinstance(text_or_el, (str, unicode)):
            for el in elements:
                children = el.getchildren()
                if children:
                    last_child = children[-1]
                    last_child.tail = (last_child.tail or '') + text_or_el
                else:
                    el.text = (el.text or '') + text_or_el
        else:
            for el in elements:
                if index is None:
                    el.append(text_or_el)
                else:
                    el.insert(index, text_or_el)

    def replace(self, path, text_or_el):
        elements = self.cssselect(path)
        if isinstance(text_or_el, (str, unicode)):
            for el in elements:
                parent = el.getparent()
                index = parent.index(el)
                parent.remove(el)
                if index:
                    children = parent.getchildren()
                    prev_child = children[index-1]
                    prev_child.tail = (prev_child.text or '') + text_or_el
                else:
                    parent.text = (parent.text or '') + text_or_el
        else:
            for el in elements:
                super(lxml.html.HtmlElement, el.getparent()).replace(el, text_or_el)

    def set_attr(self, path, attr, value):
        elements = self.cssselect(path)
        for el in elements:
            el.attrib[attr] = value

    def add_class(self, path, value):
        if path:
            elements = self.cssselect(path)
        else:
            elements = [self]
        for el in elements:
            classes = el.attrib.get('class', '').split()
            if not value in classes:
                classes.append(value)
                el.attrib['class'] = " ".join(classes)

    def after(self, path, text_or_el):
        elements = self.cssselect(path)
        for el in elements:
            if isinstance(text_or_el, (str, unicode)):
                el.tail = (el.tail or "") + text_or_el
            else:
                parent = el.getparent()
                index = parent.index(el)
                parent.insert(index+1, text_or_el)

    def before(self, path, text_or_el):
        elements = self.cssselect(path)
        for el in elements:
            if isinstance(text_or_el, (str, unicode)):
                previous = el.getprevious()
                if previous is None:
                    parent = el.getparent()
                    parent.text = (parent.text or "") + text_or_el
                else:
                    previous.tail = (previous.tail or "") + text_or_el
            else:
                parent = el.getparent()
                index = parent.index(el)
                parent.insert(index, text_or_el)

    def extract(self, path):
        elements = self.cssselect(path)
        for el in elements:
            parent = el.getparent()
            index = parent.index(el)
            children = el.getchildren()
            if el.tail:
                last_child = children[-1]
                last_child.tail = (last_child.tail or '') + el.tail
            for sub_el in reversed(children):
                parent.insert(index, sub_el)
            parent.remove(el)

    join = wiseguy.utils.join

class HtmlElementLookup(lxml.html.HtmlElementClassLookup):
    def lookup(self, node_type, document, namespace, name):
        if node_type == 'comment':
            return lxml.html.HtmlComment
        else:
            return HtmlElement

parser = lxml.html.HTMLParser()
parser.set_element_class_lookup(HtmlElementLookup())

def Html(src):
    return lxml.html.fromstring(src, parser=parser)

class JadeCompiler(pyjade.ext.html.HTMLCompiler):
    def __init__(self, node, **options):
        super(pyjade.ext.html.HTMLCompiler, self).__init__(node, **options)
        self.global_context = options.get('context', {})

def jade(src, context=None):
    import wiseguy.jade_mixins
    new_context = dict(wiseguy.jade_mixins.mixins)
    if context:
        new_context.update(context)
    text = process_jade(src, context=new_context)
    el = lxml.html.fromstring(text, parser=parser)
    return el

def process_jade(src, context=None):
    parser = pyjade.parser.Parser(src)
    block = parser.parse()
    compiler = JadeCompiler(block, pretty=False, context=context)
    return compiler.compile()

def add_generator(elem, item):
    for i in item:
        if isinstance(i, (types.ListType, types.TupleType)):
            for sub_i in i:
                elem.append(sub_i)
        else:
            elem.append(i)

_HTMLBuilder = lxml.builder.ElementMaker(
    makeelement=parser.makeelement,
    typemap={
        int: lambda e, i: str(i),
        types.GeneratorType: add_generator})

class HtmlBuilder(object):
    def __getattr__(self, key):
        return getattr(_HTMLBuilder, key.lower())
