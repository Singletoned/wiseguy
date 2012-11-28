# -*- coding: utf-8 -*-

import wiseguy.template


def test_Transform():
    r = wiseguy.template.Transform(
        "head",
        lambda context: "do something")
    assert r.keys == set(["head"])
    assert r.action("foo") == "do something"

def test_Template():
    class template(wiseguy.template.Template):
        element = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')

        transforms = [
            wiseguy.template.Transform(
                "head",
                lambda head, element: element.add("head title", "flibble")),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wobble, %s"%body))),]

    assert template.element
    assert template.transforms
    assert len(template.transforms) == 3
    assert len(template.applied_transforms) == 0

    context = dict(body="Foo")

    template.apply(context)
    assert template.keys() == set(["head"])

    html = template.element.to_string().strip()
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    assert len(template.transforms) == 1
    assert len(template.applied_transforms) == 2

    context = dict(body="Bar", head=None)
    template.apply(context)
    assert template.keys() == set()

    html = template.element.to_string().strip()
    expected = """
<html>
<head><title>flibble</title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    assert len(template.transforms) == 0
    assert len(template.applied_transforms) == 3

def test_Template_multi_transform():
    class template(wiseguy.template.Template):
        element = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')
        transforms=[
            wiseguy.template.Transform(
                "head",
                lambda head, element: element.add("head title", "flibble")),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Transform(
                ("head", "body"),
                lambda head, body, element: element.add(
                    "body div",
                    wiseguy.html.Html("%s, %s"%(head, body))))]

    template.apply(dict(head="flamble"))
    assert template.keys() == set(["body"])

    html = template.render(body="flimble").strip()
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
        element = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')
        transforms = [
            wiseguy.template.Transform(
                "head",
                lambda head, element: element.add("head title", "flibble")),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wobble, %s"%body)))]

    html = template.render(body="Foo").strip()
    assert template.keys() == set(["body", "head"])
    expected = """
<html>
<head><title></title></head>
<body><div>
<p>Wibble, Foo</p>
<p>Wobble, Foo</p>
</div></body>
</html>""".strip()
    assert html == expected

    html = template.render(body="Bar").strip()
    assert template.keys() == set(["body", "head"])
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
        element = wiseguy.html.jade("html")
        transforms = []

    class template_2(BoundTemplate):
        element = wiseguy.html.jade("html")
        transforms = []

    class template_3(BoundTemplate):
        element = wiseguy.html.jade("html")
        transforms = []

    assert template_1 in template_set
    assert template_2 in template_set
    assert template_3 in template_set


def test_Fragment():
    class fragment(wiseguy.template.Template):
        element = wiseguy.html.jade(
'''
html
  head
    title
  body
   div''')
        transforms = [
            wiseguy.template.Transform(
                "head",
                lambda head, element: element.add("head title", "flibble")),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wibble, %s"%body))),
            wiseguy.template.Transform(
                "body",
                lambda body, element: element.add("body div", wiseguy.html.Html("Wobble, %s"%body))),]

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


def test_SubTemplate():
    class master(wiseguy.template.SubTemplate):
        class flibble(wiseguy.template.Template):
            element = wiseguy.html.jade("""div: p""")
            transforms = [wiseguy.template.Transform(
                "p_content",
                lambda element, p_content: element.add("p", p_content))]

        class flamble(wiseguy.template.Template):
            element = wiseguy.html.jade("""p: span""")
            transforms = [wiseguy.template.Transform(
                "span_content",
                lambda element, span_content: element.add("span", span_content))]

    result = master(dict())
    assert len(result) == 2
    assert result['flibble'].to_string() == "<div><p></p></div>\n"
    assert result['flamble'].to_string() == "<p><span></span></p>\n"

    result = master(dict(p_content="flip flap"))
    assert len(result) == 2
    assert result['flibble'].to_string() == "<div><p>flip flap</p></div>\n"
    assert result['flamble'].to_string() == "<p><span></span></p>\n"

    result = master(dict(span_content="flim flam"))
    assert len(result) == 2
    assert result['flibble'].to_string() == "<div><p></p></div>\n"
    assert result['flamble'].to_string() == "<p><span>flim flam</span></p>\n"

    result = master(dict(p_content="flip flap", span_content="flim flam"))
    assert len(result) == 2
    assert result['flibble'].to_string() == "<div><p>flip flap</p></div>\n"
    assert result['flamble'].to_string() == "<p><span>flim flam</span></p>\n"



def test_register_template():
    template_dict = {}

    @wiseguy.template.register(template_dict)
    class template_1(wiseguy.template.Template):
        element = wiseguy.html.jade("html")
        transforms = []

    @wiseguy.template.register(template_dict)
    class template_2(wiseguy.template.Template):
        element = wiseguy.html.jade("html")
        transforms = []

    class template_3(wiseguy.template.Template):
        element = wiseguy.html.jade("html")
        transforms = []

    assert template_1 in template_dict.values()
    assert "template_1" in template_dict.keys()
    assert template_2 in template_dict.values()
    assert "template_2" in template_dict.keys()
    assert template_3 not in template_dict.values()
    assert "template_3" not in template_dict.keys()


def test_extends():
    class master(wiseguy.template.Template):
        element = wiseguy.html.jade('''
html
  head
  body''')
        transforms = [
            wiseguy.template.Transform(
                "main_body",
                lambda element, main_body: element.add("body", main_body))]

    @wiseguy.template.extends(master)
    class index(wiseguy.template.SubTemplate):
        class main_body(wiseguy.template.Template):
            element = wiseguy.html.jade('''
div
  p''')
            transforms = [
                wiseguy.template.Transform(
                    "flibble",
                    lambda element, flibble: element.add("p", flibble))]

    assert len(index.transforms) == 1
    result = index.render()
    expected = "<html>\n<head></head>\n<body><div><p></p></div></body>\n</html>\n"
    assert expected == result

def test_set_attr():
    element = wiseguy.html.jade("div: a.foo")
    set_attr = wiseguy.template.set_attr(".foo", "href", lambda bar: bar)
    set_attr(element, bar="wibble")
    result = element.normalise()
    expected = wiseguy.html.jade('div: a.foo(href="wibble")').normalise()
    assert result == expected

def test_set_text():
    element = wiseguy.html.jade("div: a.foo")
    set_text = wiseguy.template.set_text(".foo", lambda bar: bar)
    set_text(element, bar="wibble")
    result = element.normalise()
    expected = wiseguy.html.jade('div: a.foo wibble').normalise()
    assert result == expected

def test_replace():
    element = wiseguy.html.jade("div: a.foo")
    replace = wiseguy.template.replace(".foo", lambda bar: wiseguy.html.jade("div %s"%bar))
    replace(element, bar="wibble")
    result = element.normalise()
    expected = wiseguy.html.jade('div: div wibble').normalise()
    assert result == expected

def test_add():
    element = wiseguy.html.jade("div: a.foo")
    add = wiseguy.template.add(".foo", lambda bar: bar)
    add(element, bar="wibble")
    result = element.normalise()
    expected = wiseguy.html.jade('div: a.foo wibble').normalise()
    assert result == expected
