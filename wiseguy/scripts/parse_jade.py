# -*- coding: utf-8 -*-

import sys

import wiseguy.html_tidy

def main():
    arg = sys.argv[1]
    with open(arg) as f:
        content = f.read()
        return wiseguy.html_tidy.tidy_html(wiseguy.html.jade(content))

if __name__ == '__main__':
    print main()
