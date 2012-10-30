# -*- coding: utf-8 -*-

import werkzeug

import wiseguy.transforms
import wiseguy.html

def test_add_stylesheet():
    transform = wiseguy.transforms.add_stylesheet("foo.css")
    element = wiseguy.html.jade("html: head")

    assert transform.keys == set()
    transform.action(element=element)
    result = element.to_string().strip()
    expected = """
<html><head><link href="foo.css" type="text/css" rel="stylesheet"></head></html>
    """.strip()
    assert result == expected


def test_add_script():
    transform = wiseguy.transforms.add_script("foo.js")
    element = wiseguy.html.jade("html: head")

    assert transform.keys == set()
    transform.action(element=element)
    result = element.to_string().strip()
    expected = """
<html><head><script src="foo.js"></script></head></html>
    """.strip()
    assert result == expected


def test_fix_urls():
    transform = wiseguy.transforms.fix_urls()
    element = wiseguy.html.jade('''
html
  head
    link(href="/static/blueprint.css", type="text/css")
    link(href="../static/blueprint.css", type="text/css")
    script(src="/static/jquery.css")
    script(src="../static/jquery.css")
  body
    p
      img(src="/images/foo.png")
      img(src="images/foo.png")
    p
      a(href="/a_link.html?foo=bar")
      a(href="http://example.com?foo=bar")
    form(method="POST", action="/form_handler")
    form(method="POST", action="form_handler")
''')

    assert transform.keys == set(['url'])
    transform.action(
        element=element,
        url=werkzeug.Href("/mountpoint"))
    expected = '''
<html>
<head>
<link href="/mountpoint/static/blueprint.css" type="text/css">
<link href="../static/blueprint.css" type="text/css">
<script src="/mountpoint/static/jquery.css"></script><script src="../static/jquery.css"></script>
</head>
<body>
<p><img src="/mountpoint/images/foo.png"><img src="images/foo.png"></p>
<p><a href="/mountpoint/a_link.html?foo=bar"></a><a href="http://example.com?foo=bar"></a></p>
<form method="POST" action="/mountpoint/form_handler"></form>
<form method="POST" action="form_handler"></form>
</body>
</html>
'''.strip()
    result = element.to_string().strip()
    assert result == expected
