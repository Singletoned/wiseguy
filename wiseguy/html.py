# -*- coding: utf-8 -*-

import types

import pyjade.ext.html
import lxml.html

import wiseguy.utils

class HtmlElement(lxml.html.HtmlElement):
    def to_string(self, pretty=True):
        return lxml.html.tostring(self, pretty_print=pretty)

    def insert(self, path, text_or_el):
        elements = self.cssselect(path)
        if isinstance(text_or_el, (str, unicode)):
            for el in elements:
                el.text = text_or_el
        else:
            for el in elements:
                el.append(text_or_el)

    def replace(self, path, new_el):
        elements = self.cssselect(path)
        for el in elements:
            super(lxml.html.HtmlElement, el.getparent()).replace(el, new_el)

    join = wiseguy.utils.join

class HtmlElementLookup(lxml.html.HtmlElementClassLookup):
    def lookup(self, node_type, document, namespace, name):
        return HtmlElement

parser = lxml.html.HTMLParser()
parser.set_element_class_lookup(HtmlElementLookup())

def Html(src):
    return lxml.html.fromstring(src, parser=parser)

class HTMLCompiler(pyjade.compiler.Compiler):
    def attributes(self, attrs):
        return " ".join(['''%s="%s"''' % (k,v) for (k,v) in attrs.items()])

    def visitAttributes(self, attrs):
        classes = []
        params = dict()
        for attr in attrs:
            if attr['name'] == 'class':
                classes.append(attr['val'].strip("'"))
            else:
                params[attr['name']] = attr['val'].strip("'")
        if classes:
            params['class'] = " ".join(classes)
        self.buf.append("".join([''' %s="%s"''' % (k,v) for (k,v) in params.items()]))


def jade(src, context=None):
    text = process_jade(src, context=context)
    el = lxml.html.fromstring(text, parser=parser)
    return el

def process_jade(src, context=None):
    parser = pyjade.parser.Parser(src)
    block = parser.parse()
    compiler = pyjade.ext.html.HTMLCompiler(block, pretty=False, context=context)
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

