# -*- coding: utf-8 -*-

import pyjade

import wiseguy as wg
import wiseguy.html


def test_process_jade():
    "Test that Jade basically works"
    d = "div#foo.bar Hullo"
    expected = '''<div id="foo" class="bar">Hullo</div>'''
    result = wg.html.process_jade(d)
    assert expected == result

    # Test that jade works with context
    d = "div#foo.bar= foo"
    expected = '''<div id="foo" class="bar">flibble</div>'''
    result = wg.html.process_jade(d, context=dict(foo="flibble"))
    assert expected == result

def test_jade():
    d = wg.html.jade("html: body: div#main")
    assert d.tag == "html"

    expected = '''<html><body><div id="main"></div></body></html>'''
    result = d.to_string(pretty=False)
    assert result == expected

    expected = '''
<html><body><div id="main"></div></body></html>'''.strip()
    result = d.to_string().strip()
    assert result == expected

def test_tidy():
    d = wg.html.jade("html: body: div#main foo")
    expected = '''
<!DOCTYPE html>
<html>
  <body>
    <div id="main">
      foo
    </div>
  </body>
</html>
'''.strip()
    result = d.to_string(tidy=True)
    assert result == expected

def test_template_add():
    template = """
html
  head
    title
  body
    h1#title placeholder text
    div#body"""
    t = wg.html.jade(template)
    t.add("title, #title", "Hullo Mr Flibble")
    t.add("#body", wg.html.Html("<span class='bar'>Welcome to my web</span>"))
    t.add("body", wg.html.Html("<span>This goes before the header</span>"), index=0)

    result = t.to_string().strip()
    expected = '''
<html>
<head><title>Hullo Mr Flibble</title></head>
<body>
<span>This goes before the header</span><h1 id="title">Hullo Mr Flibble</h1>
<div id="body"><span class="bar">Welcome to my web</span></div>
</body>
</html>'''.strip()
    assert expected == result

def test_template_replace():
    template = """
html
  body
    h1#title placeholder text
    div#body
    div
      div.content-1
    div
      div.placeholder
      div.content-2
"""
    t = wg.html.jade(template)
    t.replace("#title", wg.html.jade("h1#title Hullo Mr Flibble"))
    t.replace("#body", wg.html.Html("<span class='bar'>Welcome to my web</span>"))
    t.replace("div.content-1", "Hullo Again")
    t.replace("div.content-2", "Hullo Again")

    result = t.to_string().strip()
    expected = '''
<html><body>
<h1 id="title">Hullo Mr Flibble</h1>
<span class="bar">Welcome to my web</span><div>Hullo Again</div>
<div>
<div class="placeholder"></div>Hullo Again</div>
</body></html>'''.strip()
    assert expected == result

def test_template_add_class():
    element = wg.html.jade("div: span.foo")
    element.add_class("span", "foo")
    result = element.to_string().strip()
    expected = '''<div><span class="foo"></span></div>'''
    assert expected == result

    element.add_class("span", "bar")
    result = element.to_string().strip()
    expected = '''<div><span class="foo bar"></span></div>'''
    assert expected == result

    element.add_class(None, "baz")
    result = element.to_string().strip()
    expected = '''<div class="baz"><span class="foo bar"></span></div>'''
    assert expected == result

def test_template_after():
    element = wg.html.jade('''
div
  p.foo
  p.bar''')
    element.after("p.foo", wg.html.jade("p.woosit"))
    result = element.to_string().strip()
    expected = '''
<div>
<p class="foo"></p>
<p class="woosit"></p>
<p class="bar"></p>
</div>'''.strip()
    assert expected == result

    element.after("p.foo", "Flooble")
    result = element.to_string().strip()
    expected = '''
<div>
<p class="foo"></p>Flooble<p class="woosit"></p>
<p class="bar"></p>
</div>'''.strip()
    assert expected == result

def test_template_before():
    element = wg.html.jade('''
div
  p.foo
  p.bar''')
    element.before("p.bar", wg.html.jade("p.woosit"))
    result = element.to_string().strip()
    expected = '''
<div>
<p class="foo"></p>
<p class="woosit"></p>
<p class="bar"></p>
</div>'''.strip()
    assert expected == result

    element.before("p.bar", "Flooble")
    result = element.to_string().strip()
    expected = '''
<div>
<p class="foo"></p>
<p class="woosit"></p>Flooble<p class="bar"></p>
</div>'''.strip()
    assert expected == result

    element.before("p.foo", "Flibble")
    result = element.to_string().strip()
    expected = '''
<div>Flibble<p class="foo"></p>
<p class="woosit"></p>Flooble<p class="bar"></p>
</div>'''.strip()
    assert expected == result

def test_extract():
    element = wg.html.jade("""
html
  body
    div
      div#one
      block
        div#two.one
        div#two.two
        | flibble
      | some tail
      div#three
""")
    element.extract("block")
    result = element.to_string().strip()
    expected = '''
<html><body><div>
<div id="one"></div>
<div id="two" class="one"></div>
<div id="two" class="two"></div>flibble
some tail
<div id="three"></div>
</div></body></html>
'''.strip()
    wg.utils.print_quick_pprint_diff(expected, result)
    assert expected == result

def test_HTMLBuilder():
    def gen_elements():
        yield wg.html._HTMLBuilder.p()
        yield (wg.html._HTMLBuilder.br(), wg.html._HTMLBuilder.span())

    element = wg.html._HTMLBuilder.div(gen_elements())
    result = [el.tag for el in element]
    expected = ["p", "br", "span"]
    assert expected == result

def test_HtmlElement():
    h = wg.html.HtmlBuilder()
    data = [
        wg.html.Html("<p>One</p>"),
        wg.html.Html("<p>Two</p>"),
        wg.html.Html("<p>Three</p>")]
    expected = '''
<div>
<p>One</p>
<br><p>Two</p>
<br><p>Three</p>
</div>
    '''.strip()
    result = h.DIV(
        wg.html.Html("<br>").join(data)).to_string().strip()
    assert expected == result
