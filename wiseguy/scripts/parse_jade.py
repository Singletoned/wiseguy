# -*- coding: utf-8 -*-

import sys

import path

import wiseguy.html_tidy
import wiseguy.html


def main():
    args = sys.argv[1:]
    for arg in args:
        f_in = path.path(arg)
        f_out = f_in.parent.child(f_in.namebase + ".html")
        jade_content = f_in.text('utf8')
        html_content = wiseguy.html_tidy.tidy_html(wiseguy.html.jade(jade_content))
        f_out.write_text(html_content, 'utf8')

if __name__ == '__main__':
    main()
