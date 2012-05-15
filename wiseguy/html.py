# -*- coding: utf-8 -*-

import pyjade

import lxml.html

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


def jade(src):
    text = process_jade(src)
    el = lxml.html.fromstring(text)
    return el

def process_jade(src):
    parser = pyjade.parser.Parser(src)
    block = parser.parse()
    compiler = HTMLCompiler(block)
    return compiler.compile()
