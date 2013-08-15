#! python
# -*- coding: utf-8 -*-

import sys

import path

import wiseguy.html2jade
import wiseguy.html


def main():
    args = sys.argv[1:]
    for arg in args:
        f_in = path.path(arg)
        f_out = f_in.parent.child(f_in.namebase + ".jade")
        html_content = f_in.text('utf8')
        jade_content = wiseguy.html2jade.html2jade(html_content)
        f_out.write_text(jade_content, 'utf8')

if __name__ == '__main__':
    print main()
