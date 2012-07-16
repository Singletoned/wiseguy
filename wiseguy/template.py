# -*- coding: utf-8 -*-

import collections


class Rule(object):
    def __init__(self, key, transform):
        self.key = key
        self.transform = transform

class RuleMap(object):
    def __init__(self, *args):
        self.rules = collections.defaultdict(list)
        for rule in args:
            self.rules[rule.key].append(rule.transform)

class Template(object):
    def __init__(self, template, rules):
        self.template = template
        self.rules = rules
