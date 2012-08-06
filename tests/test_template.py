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
            lambda head, template: template.insert("head title", "flibble")),
        wiseguy.template.Rule(
            "body",
            lambda body, template: template.insert("body div", wiseguy.html.Html("Wibble, %s"%body))),
        wiseguy.template.Rule(
            "body",
            lambda body, template: template.insert("body div", wiseguy.html.Html("Wobble, %s"%body))),
])
    assert template.template
    assert template.rules
    assert len(template.rules['head']) == 1
    assert len(template.rules['body']) == 2

    context = dict(body="Foo")

    template.apply(context)

    html = template.template.to_string().strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    assert len(template.rules['head']) == 1
    assert len(template.rules['body']) == 0

    context = dict(body="Bar", head=None)
    template.apply(context)

    html = template.template.to_string().strip()
    expected = """
<html>
<head><title>flibble</title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    assert len(template.rules['head']) == 0
    assert len(template.rules['body']) == 0

def test_Template_multiple_renderings():
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
            lambda head, template: template.insert("head title", "flibble")),
        wiseguy.template.Rule(
            "body",
            lambda body, template: template.insert("body div", wiseguy.html.Html("Wibble, %s"%body))),
        wiseguy.template.Rule(
            "body",
            lambda body, template: template.insert("body div", wiseguy.html.Html("Wobble, %s"%body)))])
    html = template(body="Foo").strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    html = template(body="Bar").strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Bar</p>
<p>Wobble, Bar</p>
</div></body>
</html>""".strip()
    assert html == expected


def test_bound_template():
    template_set = set()
    Template = wiseguy.template.bound_template(template_set.add)

    template_1 = Template(wiseguy.html.jade("html"), [])
    template_2 = Template(wiseguy.html.jade("html"), [])
    template_3 = Template(wiseguy.html.jade("html"), [])

    assert template_1 in template_set
    assert template_2 in template_set
    assert template_3 in template_set
