# -*- coding: utf-8 -*-

import collections


class Rule(object):
    def __init__(self, key, transform):
        self.key = key
        self.transform = transform

class Template(object):
    def __init__(self, template, rules):
        self.template = template
        self.rules = collections.defaultdict(list)
        for rule in rules:
            self.rules[rule.key].append(rule.transform)

    def apply(self, context):
        for key in self.rules.iterkeys():
            if key in context:
                while self.rules[key]:
                    rule = self.rules[key].pop(0)
                    rule(context[key], self.template)
