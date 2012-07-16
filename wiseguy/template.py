# -*- coding: utf-8 -*-


class Rule(object):
    def __init__(self, key, transform):
        self.key = key
        self.transform = transform

class Template(object):
    def __init__(self, template, rules):
        self.template = template
        self.rules = rules
