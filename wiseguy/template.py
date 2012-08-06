# -*- coding: utf-8 -*-

import collections, copy

import lxml.html

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

    def copy(self):
        return Template(
            copy.deepcopy(self.template),
            [Rule(key, transform) for key in self.rules.iterkeys() for transform in self.rules[key]])

    def __call__(self, **kwargs):
        template = self.copy()
        template.apply(kwargs)
        return lxml.html.tostring(template.template, pretty_print=True)

def bound_template(adder_func):
    class BoundTemplate(Template):
        def __init__(self, template, rules):
            adder_func(self)
            super(BoundTemplate, self).__init__(template, rules)
    return BoundTemplate
