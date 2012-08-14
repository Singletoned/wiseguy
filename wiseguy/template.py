# -*- coding: utf-8 -*-

import collections, copy, functools

import lxml.html

class Rule(object):
    def __init__(self, key, transform):
        if isinstance(key, basestring):
            self.key = frozenset([key])
        else:
            self.key = frozenset(key)
        self.transform = transform

class Template(object):
    def __init__(self, template, rules):
        self.template = template
        self.rules = collections.defaultdict(list)
        for rule in rules:
            self.rules[rule.key].append(rule.transform)

    def _pop_keys(self, key, context):
        kwargs = dict([(k, context[k]) for k in key])
        while self.rules[key]:
            rule = self.rules[key].pop(0)
            rule(template=self.template, **kwargs)

    def apply(self, context):
        completed_keys = []
        for key in self.rules.keys():
            ctx_keys = set(context.iterkeys())
            shared_keys = key & ctx_keys
            if shared_keys:
                if key <= ctx_keys:
                    self._pop_keys(key, context)
                else:
                    kwargs = dict([(k, context[k]) for k in shared_keys])
                    different_keys = key - ctx_keys
                    self.rules[tuple(different_keys)] = [
                        functools.partial(r, **kwargs)
                        for r in self.rules[key]]

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
