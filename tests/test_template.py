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
            "head",
            lambda head, template: template.insert("head", wiseguy.html.Html("flibble"))),
        wiseguy.template.Rule(
            "body",
            lambda head, template: template.insert("body div", wiseguy.html.Html("Wibble"))),
        wiseguy.template.Rule(
            "body",
            lambda head, template: template.insert("body div", wiseguy.html.Html("Wobble"))),
])
    assert template.template
    assert template.rules
    assert len(template.rules['head']) == 1
    assert len(template.rules['body']) == 2

    context = dict(body=None)

    template.apply(context)

    html = template.template.to_string().strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble</p>
<p>Wobble</p>
</div></body>
</html>""".strip()
    assert html == expected

    assert len(template.rules['head']) == 1
    assert len(template.rules['body']) == 0
