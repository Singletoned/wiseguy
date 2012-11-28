# -*- coding: utf-8 -*-

import urlparse

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
        [],
        lambda element: element.add(
            "head",
            stylesheet(href)))

def add_script(href):
    return Transform(
        [],
        lambda element: element.add(
            "head",
            script(href)))

_url_fixable_tags = set([
    ("link", "href"),
    ("script", "src"),
    ("a", "href"),
    ("form", "action"),
    ("img", "src"),
])

def _fix_urls(element, url):
    for (tag, attr) in _url_fixable_tags:
        path = css("%s[%s]" % (tag, attr))
        for el in element.xpath(path):
            value = el.attrib[attr]
            parts = urlparse.urlparse(value)
            if (not parts.netloc) and (parts.path.startswith("/")):
                new_url = urlparse.urlunparse((
                    parts.scheme,
                    parts.netloc,
                    url(parts.path),
                    parts.params,
                    parts.query,
                    parts.fragment))
                el.attrib[attr] = new_url

def fix_urls():
    return Transform(
        "url",
        lambda element, url: _fix_urls(element, url))
