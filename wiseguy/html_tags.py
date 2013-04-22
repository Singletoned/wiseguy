# -*- coding: utf-8 -*-

import lxml.etree

import wiseguy.html


Comment = lxml.etree.Comment

builder = wiseguy.html.HtmlBuilder()


HTML = builder.html
HEAD = builder.head
LINK = builder.link
META = builder.meta
STYLE = builder.style
SCRIPT = builder.script
BODY = builder.body
TABLE = builder.table
TR = builder.tr
TD = builder.td
IMG = builder.img
SPAN = builder.span
DIV = builder.div
BR = builder.br
P = builder.p
A = builder.a
SELECT = builder.select
OPTION = builder.option
INPUT = builder.input
LABEL = builder.label
UL = builder.ul
LI = builder.li
BUTTON = builder.button
FORM = builder.FORM
