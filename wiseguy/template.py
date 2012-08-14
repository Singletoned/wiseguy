# -*- coding: utf-8 -*-

import collections, copy, functools

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

    def _pop_keys(self, key, context):
        if isinstance(key, tuple):
            kwargs = dict([(k, context[k]) for k in key])
        else:
            kwargs = dict([(key, context[key])])
        while self.rules[key]:
            rule = self.rules[key].pop(0)
            rule(template=self.template, **kwargs)

    def apply(self, context):
        completed_keys = []
        for key in self.rules.keys():
            if isinstance(key, tuple):
                key_set = set(key)
                ctx_keys = set(context.iterkeys())
                shared_keys = key_set & ctx_keys
                if shared_keys:
                    if key_set <= ctx_keys:
                        self._pop_keys(key, context)
                    else:
                        kwargs = dict([(k, context[k]) for k in shared_keys])
                        different_keys = key_set - ctx_keys
                        self.rules[tuple(different_keys)] = [
                            functools.partial(r, **kwargs)
                            for r in self.rules[key]]
            elif key in context:
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
