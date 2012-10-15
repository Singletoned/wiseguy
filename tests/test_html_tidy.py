# -*- coding: utf-8 -*-

import unittest

import wiseguy as wg
import wiseguy.html_tidy
import wiseguy.html


class Test_normalise_html(unittest.TestCase):
    def test_normalise_html(self):
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

    def test_nbsp(self):
        t = wg.html.Html('''
<p>&nbsp;<span>&nbsp;&nbsp;&nbsp;&nbsp;</span>&nbsp;</p>''')
        expected = '''
<p>
&#160;
<span>
&#160;&#160;&#160;&#160;
</span>
&#160;
</p>'''.strip()
        result = wg.html_tidy.normalise_html(t).strip()
        assert result == expected

    def test_empty_tag_with_tail(self):
        t = wg.html.Html('''<p>Hello<img>World</p>''')
        expected= '''
<p>
Hello
<img>
World
</p>'''.strip()
        result = wg.html_tidy.normalise_html(t).strip()
        assert result == expected


class Test_render_inline_tag(unittest.TestCase):
    def test_span(self):
        data = '''
<span>Hullo 
<strong>World
</strong>! 
<br>The End</span>'''
        result = wg.html_tidy._render_inline_tag(wg.html.Html(data)).next().strip()
        expected = '''<span>Hullo <strong>World</strong>! <br>The End</span>'''.strip()
        assert result == expected

    def test_span_in_para(self):
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

    def test_nbsp(self):
        data = '''
<p>&nbsp;<span>&nbsp;&nbsp;&nbsp;&nbsp;</span>&nbsp;</p>'''
        expected = '''
<p>&#160;<span>&#160;&#160;&#160;&#160;</span>&#160;</p>'''.strip()
        result = wg.html_tidy._render_inline_tag(wg.html.Html(data)).next().strip()
        assert result == expected

    def test_comment(self):
        data = '''
<p><!-- Flibble -->This is not a comment</p>'''
        expected = '''<p><!-- Flibble -->This is not a comment</p>'''
        result = wg.html_tidy._render_inline_tag(wg.html.Html(data)).next().strip()
        assert result == expected

class Test_render_block_tag(unittest.TestCase):
    def test_empty_tag(self):
        data = '''<div></div>'''
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        expected = '''
<div></div>
'''.strip()
        assert result == expected

    def test_with_tail(self):
        data = '''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End</div>'''
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        expected = '''
<div class="bar" id="foo" style="bloop">
  Hullo <strong>World!</strong><br>The End
</div>
'''.strip()
        assert result == expected

    def test_with_inline_tag(self):
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

    def test_nbsp(self):
        data = '''
<p>&nbsp;<span>&nbsp;&nbsp;&nbsp;&nbsp;</span>&nbsp;</p>'''
        expected = '''
<p>
  &#160;<span>&#160;&#160;&#160;&#160;</span>&#160;
</p>'''.strip()
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        assert result == expected

    def test_render_empty_tag_with_tail(self):
        data = '''<div>Hello<img>World'''
        expected= '''
<div>
  Hello<img>World
</div>'''.strip()
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        assert result == expected

    def test_render_non_empty_block_tag_with_tail(self):
        data = '''<div>Hello<div>Mr</div>Flibble</div>'''
        expected= '''
<div>
  Hello
  <div>
    Mr
  </div>
  Flibble
</div>'''.strip()
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        assert result == expected

    def test_render_empty_block_tag_with_tail(self):
        data = '''<div>Hello<div></div>World</div>'''
        expected= '''
<div>
  Hello
  <div></div>
  World
</div>'''.strip()
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        assert result == expected

    def test_image(self):
        data = '''
<p>Pre-image<img>Post-image</p>'''
        expected = '''
<p>
  Pre-image<img>Post-image
</p>
'''.strip()
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        assert result == expected

    def test_comment(self):
        data = '''
<p><!-- Flibble -->This is not a comment</p>'''
        expected = '''
<p>
  <!-- Flibble -->
  This is not a comment
</p>'''.strip()
        result = "\n".join(wg.html_tidy._render_block_tag(wg.html.Html(data))).strip()
        assert result == expected

class Test_tidy_html(unittest.TestCase):
    def test_fragment(self):
        t = wg.html.Html(
u'''<div id="foo" class="bar" style="bloop"> Hullo <strong>World!</strong><br>The End£</div>''')
        result = wg.html_tidy.tidy_html(t).strip()
        expected = '''
<div class="bar" id="foo" style="bloop">
  Hullo <strong>World!</strong><br>The End&#163;
</div>
'''.strip()
        assert result == expected

    def test_document(self):
        t = wg.html.Html(
u'''
<html lang="en">
<head>
<title>
A Form£
</title>
</head>
<body>
<!-- And thus it begins... -->
<form>
<fieldset>
<legend>
<!-- Not the legend of King Arthur! -->
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
    <title>A Form&#163;</title>
  </head>
  <body>
    <!-- And thus it begins... -->
    <form>
      <fieldset>
        <legend><!-- Not the legend of King Arthur! -->Your Information</legend>
        <div class="control-group">
          <label class="control-label" for="name">Name:</label>
          <input id="name">
        </div>
      </fieldset>
    </form>
  </body>
</html>'''.strip()
        assert result == expected

    def test_nbsp(self):
        t = wg.html.Html('''
<p>&nbsp;<span>&nbsp;&nbsp;&nbsp;&nbsp;</span>&nbsp;</p>''')
        expected = '''
<p>
  &#160;<span>&#160;&#160;&#160;&#160;</span>&#160;
</p>'''.strip()
        result = wg.html_tidy.tidy_html(t).strip()
        assert result == expected
