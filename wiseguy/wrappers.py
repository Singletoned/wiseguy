# -*- coding: utf-8 -*-

def add_class(element, class_name):
    classes = element.attrib.get('class', "").split()
    classes.append(class_name)
    element.attrib['class'] = " ".join(classes)

def span(length, element):
    _input = element.xpath('//input')[0]
    add_class(_input, 'span%s'%length)
    return element

def compulsory(element):
    _label = element.xpath("//label")[0]
    _label.text = _label.text + "*"
    return element
