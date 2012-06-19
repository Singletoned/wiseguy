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

def test_template_insert():
    template = """
html
  head
    title
  body
    h1#title | placeholder text
    div#body"""
    t = wg.html.jade(template)
    t.insert("title, #title", "Hullo Mr Flibble")
    t.insert("#body", wg.html.Html("<span class='bar'>Welcome to my web</span>"))

    result = t.to_string().strip()
    expected = '''
<html>
<head><title>Hullo Mr Flibble</title></head>
<body>
<h1 id="title">Hullo Mr Flibble</h1>
<div id="body"><span class="bar">Welcome to my web</span></div>
</body>
</html>'''.strip()
    assert expected == result

def test_normalise_html():
    t = wg.html.Html('''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End</div>''')
    result = wg.html.normalise_html(t).strip()
    expected = '''
<div class="bar" id="foo" style="bloop">
Hullo
<strong>
World!
</strong>
<br>
The End
</div>
'''.strip()
    assert result == expected

def test_render_inline_tag():
    data = '''
<span>Hullo 
<strong>World
</strong>! 
<br>The End</span>'''
    result = wg.html._render_inline_tag(wg.html.Html(data)).next().strip()
    expected = '''<span>Hullo <strong>World</strong>! <br>The End</span>'''.strip()
    assert result == expected

    data = '''
<p><span>Hullo 
<strong>
 World
</strong>! 
<br>The End</span>

</p>'''
    result = wg.html._render_inline_tag(wg.html.Html(data)).next().strip()
    expected = '''<p><span>Hullo <strong> World</strong>! <br>The End</span></p>'''.strip()
    assert result == expected

def test_render_block_tag():
    data = '''<div></div>'''
    result = "\n".join(wg.html._render_block_tag(wg.html.Html(data))).strip()
    expected = '''
<div></div>
'''.strip()
    assert result == expected

    data = '''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End</div>'''
    result = "\n".join(wg.html._render_block_tag(wg.html.Html(data))).strip()
    expected = '''
<div class="bar" id="foo" style="bloop">
  Hullo <strong>World!</strong><br>The End
</div>
'''.strip()
    assert result == expected

    data = '''
<html lang="en">
<head>
<title>
A Form
</title> </head> <body></body>
    '''.strip()
    result = "\n".join(wg.html._render_block_tag(wg.html.Html(data))).strip()
    expected = '''
<html lang="en">
  <head>
    <title>A Form</title>
  </head>
  <body></body>
</html>'''.strip()
    assert result == expected

def test_tidy_html():
    t = wg.html.Html('''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End</div>''')
    result = wg.html.tidy_html(t).strip()
    expected = '''
<div class="bar" id="foo" style="bloop">
  Hullo <strong>World!</strong><br>The End
</div>
'''.strip()
    assert result == expected

    t = wg.html.Html(
'''
<html lang="en">
<head>
<title>
A Form
</title>
</head>
<body>
<form>
<fieldset>
<legend>
Your Information
</legend>
<div class="control-group">
<label class="control-label" for="name">
Name:
</label>
<input id="name">
</div>''')
    result = wg.html.tidy_html(t).strip()

    expected = '''
<html lang="en">
  <head>
    <title>A Form</title>
  </head>
  <body>
    <form>
      <fieldset>
        <legend>Your Information</legend>
        <div class="control-group">
          <label class="control-label" for="name">Name:</label>
          <input id="name">
        </div>
      </fieldset>
    </form>
  </body>
</html>'''.strip()
    assert result == expected
