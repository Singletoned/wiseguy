# -*- coding: utf-8 -*-

import wiseguy.template


def test_Rule():
    r = wiseguy.template.Rule(
        "head",
        lambda context: "do something")
    assert r.key == "head"
    assert r.transform("foo") == "do something"

def test_RuleMap():
    rm = wiseguy.template.RuleMap(
        wiseguy.template.Rule(
            "head",
            lambda context: context['head'].upper()),
        wiseguy.template.Rule(
            "body",
            lambda context: context['body'].upper()),
        wiseguy.template.Rule(
            "body",
            lambda context: context['body'].lower()))
    assert rm.rules
    assert len(rm.rules['head']) == 1
    assert len(rm.rules['body']) == 2

def test_Template():
    template = wiseguy.template.Template(
        wiseguy.html.jade(
'''
html
  head
    title
  body
   div'''),
    rules=[wiseguy.template.Rule("head", lambda context: "do something")])
    assert template.template
    assert template.rules
