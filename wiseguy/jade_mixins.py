# -*- coding: utf-8 -*-

from wiseguy import html_tags as ht


mixins = dict()

def register(func):
    mixins[func.__name__] = func
    return func

@register
def select(id, options, selected=None, blank_option=False):
    option_elements = []
    if blank_option:
        o = ht.OPTION(value="")
        option_elements.append(o)
    for option in options:
        if isinstance(option, (list, tuple)):
            value, text = option
        else:
            value, text = (option, option)
        value = unicode(value)
        text = unicode(text)
        if value == selected:
            o = ht.OPTION(text, value=value, selected="selected")
        else:
            o = ht.OPTION(text, value=value)
        print repr(value), repr(text)
        option_elements.append(o)
    element = ht.SELECT(
        *option_elements,
        name=id,
        id=id)
    return element.to_string()
