# -*- coding: utf-8 -*-

from wiseguy import html2jade

import path


test_dir = path.path(__file__).dirname()
html2jade_dir = test_dir.child("test_html2jade_cases")

case_names = set(f.namebase for f in html2jade_dir.files())

def test_simple():
    def do_test(case_name):
        html = html2jade_dir.child("%s.html"%case_name).text('utf8')
        expected = html2jade_dir.child("%s.jade"%case_name).text('utf8')
        result = html2jade.html2jade(html)
        assert result == expected

    for case_name in case_names:
        yield do_test, case_name
