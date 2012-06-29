# -*- coding: utf-8 -*-

import wiseguy as wg
import wiseguy.html_tidy
import wiseguy.html


def test_normalise_html():
    t = wg.html.Html('''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End</div>''')
    result = wg.html_tidy.normalise_html(t).strip()
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
    result = wg.html_tidy._render_inline_tag(wg.html.Html(data)).next().strip()
    expected = '''<span>Hullo <strong>World</strong>! <br>The End</span>'''.strip()
    assert result == expected

    data = '''
<p><span>Hullo 
<strong>
 World
</strong>! 
<br>The End</span>

</p>'''
    result = wg.html_tidy._render_inline_tag(wg.html.Html(data)).next().strip()
    expected = '''<p><span>Hullo <strong> World</strong>! <br>The End</span></p>'''.strip()
    assert result == expected

def test_render_block_tag():
    data = '''<div></div>'''
    result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
    expected = '''
<div></div>
'''.strip()
    assert result == expected

    data = '''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End</div>'''
    result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
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
    result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
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
    result = wg.html_tidy.tidy_html(t).strip()
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
    result = wg.html_tidy.tidy_html(t).strip()

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
