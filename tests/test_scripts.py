# -*- coding: utf-8 -*-

import sys

import path

import wiseguy.scripts.parse_jade



def test_parse_jade():
    data = "html: body: div#main"
    expected = '''
<html>
  <body>
    <div id="main"></div>
  </body>
</html>'''.strip()
    with path.create_temp_file(data) as filepath:
        with path.temp_sys_argv("python", filepath):
            result = wiseguy.scripts.parse_jade.main()
    assert expected == result
