# -*- coding: utf-8 -*-

import sys

import path

import wiseguy.scripts.parse_jade



def test_parse_jade():
    jade_input = "html: body: div#main"
    html_expected = '''
<html>
  <body>
    <div id="main"></div>
  </body>
</html>'''.strip()
    with path.create_temp_dir() as temp_dir:
        temp_html = temp_dir.child("test.html")
        temp_jade = temp_dir.child("test.jade")
        temp_jade.write_text(jade_input)
        with path.temp_sys_argv("python", temp_jade):
            wiseguy.scripts.parse_jade.main()
        assert temp_html.text() == html_expected
