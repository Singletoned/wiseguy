# -*- coding: utf-8 -*-

import collections, copy, functools

import lxml.html

class Rule(object):
    def __init__(self, keys, transform):
        if isinstance(keys, basestring):
            self.keys = set([keys])
        else:
            self.keys = set(keys)
        self.transform = transform
        self.applied = False
        self.context = dict()

    def __repr__(self):
        return "<Rule %s>" % self.keys

    def apply(self, context):
        for key in list(self.keys):
            if key in context:
                self.context[key] = context[key]
                self.keys.remove(key)
        if not self.keys:
            self.applied = True

class Template(object):
    def __init__(self, template, rules):
        self.template = template
        self.rules = rules
        self.applied_rules = []

    def _pop_keys(self, key, context):
        kwargs = dict([(k, context[k]) for k in key])
        while self.rules[key]:
            rule = self.rules[key].pop(0)
            rule(template=self.template, **kwargs)

    def apply(self, context):
        for rule in list(self.rules):
            rule.apply(context)
            if rule.applied:
                rule.transform(template=self.template, **rule.context)
                self.rules.remove(rule)
                self.applied_rules.append(rule)

    def copy(self):
        return Template(
            copy.deepcopy(self.template),
            copy.deepcopy(self.rules))

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
