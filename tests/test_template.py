# -*- coding: utf-8 -*-

import wiseguy.template


def test_Rule():
    r = wiseguy.template.Rule(
        "head",
        lambda context: "do something")
    assert r.keys == set(["head"])
    assert r.transform("foo") == "do something"

def test_Template():
    class template(wiseguy.template.Template):
        template = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')

        rules = [
            wiseguy.template.Rule(
                "head",
                lambda head, template: template.insert("head title", "flibble")),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wobble, %s"%body))),]

    assert template.template
    assert template.rules
    assert len(template.rules) == 3
    assert len(template.applied_rules) == 0

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

    assert len(template.rules) == 1
    assert len(template.applied_rules) == 2

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

    assert len(template.rules) == 0
    assert len(template.applied_rules) == 3

def test_Template_multi_rule():
    class template(wiseguy.template.Template):
        template = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')
        rules=[
            wiseguy.template.Rule(
                "head",
                lambda head, template: template.insert("head title", "flibble")),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Rule(
                ("head", "body"),
                lambda head, body, template: template.insert(
                    "body div",
                    wiseguy.html.Html("%s, %s"%(head, body))))]

    template.apply(dict(head="flamble"))
    html = template(body="flimble").strip()
    expected = """
<html>
<head><title>flibble</title></head>
<body><div>
<p>Wibble, flimble</p>
<p>flamble, flimble</p>
</div></body>
</html>""".strip()
    assert html == expected


def test_Template_multiple_renderings():
    class template(wiseguy.template.Template):
        template = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')
        rules = [
            wiseguy.template.Rule(
                "head",
                lambda head, template: template.insert("head title", "flibble")),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wobble, %s"%body)))]

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
    BoundTemplate = wiseguy.template.bound_template(template_set.add)

    class template_1(BoundTemplate):
        template = wiseguy.html.jade("html")
        rules = []

    class template_2(BoundTemplate):
        template = wiseguy.html.jade("html")
        rules = []

    class template_3(BoundTemplate):
        template = wiseguy.html.jade("html")
        rules = []

    assert template_1 in template_set
    assert template_2 in template_set
    assert template_3 in template_set


def test_Fragment():
    class fragment(wiseguy.template.Fragment):
        template = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')
        rules = [
            wiseguy.template.Rule(
                "head",
                lambda head, template: template.insert("head title", "flibble")),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Rule(
                "body",
                lambda body, template: template.insert("body div", wiseguy.html.Html("Wobble, %s"%body))),]

    html = fragment(dict(body="Foo")).to_string().strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    html = fragment(dict(body="Bar")).to_string().strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Bar</p>
<p>Wobble, Bar</p>
</div></body>
</html>""".strip()
    assert html == expected


def test_register_template():
    template_dict = {}

    @wiseguy.template.register(template_dict)
    class template_1(wiseguy.template.Template):
        template = wiseguy.html.jade("html")
        rules = []

    @wiseguy.template.register(template_dict)
    class template_2(wiseguy.template.Template):
        template = wiseguy.html.jade("html")
        rules = []

    class template_3(wiseguy.template.Template):
        template = wiseguy.html.jade("html")
        rules = []

    assert template_1 in template_dict.values()
    assert "template_1" in template_dict.keys()
    assert template_2 in template_dict.values()
    assert "template_2" in template_dict.keys()
    assert template_3 not in template_dict.values()
    assert "template_3" not in template_dict.keys()


def test_extends():
    def extension(foo, bar):
        assert foo == "flamble"
        assert bar == "flibble"

    @wiseguy.template.extends(extension)
    def my_func(foo, bar="flibble"):
        return dict(foo=foo, bar=bar)

    my_func(foo="flamble")
