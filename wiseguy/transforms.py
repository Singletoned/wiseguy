# -*- coding: utf-8 -*-

import cssselect
css = cssselect.HTMLTranslator().css_to_xpath

from wiseguy import html_tags as ht
from wiseguy.template import Transform


def stylesheet(href):
    return ht.LINK(
        {
            'rel': "stylesheet",
            'type': "text/css",
            'href': href})

def script(href):
    return ht.SCRIPT({'src': href})

def add_stylesheet(href):
    return Transform(
        "url",
        lambda element, url: element.insert(
            "head",
            stylesheet(
                url(href))))

def add_script(href):
    return Transform(
        "url",
        lambda element, url: element.insert(
            "head",
            script(
                url(href))))

_url_fixable_tags = set([
    ("link", "href"),
    ("script", "src"),
    ("a", "href"),
    ("form", "action")
])

def _fix_urls(element, url):
    for (tag, attr) in _url_fixable_tags:
        path = css("%s[%s]" % (tag, attr))
        for el in element.xpath(path):
            if el.attrib[attr].startswith("/"):
                el.attrib[attr] = url(el.attrib[attr])

def fix_urls():
    return Transform(
        "url",
        lambda element, url: _fix_urls(element, url))
