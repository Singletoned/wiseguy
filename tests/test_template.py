# -*- coding: utf-8 -*-

import wiseguy.template


def test_Rule():
    r = wiseguy.template.Rule(
        "head",
        lambda context: "do something")
    assert r.key == "head"
    assert r.transform("foo") == "do something"

def test_Template():
    template = wiseguy.template.Template(
        wiseguy.html.jade(
'''
html
  head
    title
  body
   div'''),
    rules=[
        wiseguy.template.Rule(
            "head", lambda context: "do something")])
    assert template.template
    assert template.rules
