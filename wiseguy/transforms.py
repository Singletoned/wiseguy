# -*- coding: utf-8 -*-

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