# -*- coding: utf-8 -*-

def add_class(element, class_name):
    classes = element.attrib.get('class', "").split()
    classes.append(class_name)
    element.attrib['class'] = " ".join(classes)
