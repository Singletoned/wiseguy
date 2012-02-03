# -*- coding: utf-8 -*-

def _add_class(element, class_name):
    classes = element.attrib.get('class', "").split()
    classes.append(class_name)
    element.attrib['class'] = " ".join(classes)

def span(element, length):
    _input = element.xpath('//input')[0]
    _add_class(_input, 'span%s'%length)
    return element

def compulsory(element):
    _label = element.xpath("//label")[0]
    _label.text = _label.text + "*"
    return element

def with_class(element, path, class_name):
    els = element.xpath(path)
    for el in els:
        _add_class(el, class_name)
    return element
