# -*- coding: utf-8 -*-

import collections, copy, functools, contextlib

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

class TemplateMeta(type):
    applied_rules = []

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
        return TemplateMeta(
            'Template',
            (Template,),
            dict(
                template=copy.deepcopy(self.template),
                rules=copy.deepcopy(self.rules)))

    def render_lxml(self, **kwargs):
        template = self.copy()
        template.apply(kwargs)
        return template.template

    def __call__(self, kwargs):
        html = self.render_lxml(**kwargs)
        return lxml.html.tostring(html, pretty_print=True)


class Template(object):
    __metaclass__ = TemplateMeta

class FragmentMeta(TemplateMeta):
    def __call__(self, context):
        return self.render_lxml(**context)

class Fragment(object):
    __metaclass__ = FragmentMeta

class SubTemplateMeta(TemplateMeta):
    def __init__(self, cls_name, bases, cls_dict):
        self.keys = [k for k in cls_dict if not k.startswith("_")]

    def __call__(self, context):
        return dict(
            (k, getattr(self, k).render_lxml(**context)) for k in self.keys)

class SubTemplate(object):
    __metaclass__ = SubTemplateMeta


def bound_template(adder_func):
    class BoundTemplateMeta(TemplateMeta):
        def __init__(cls, cls_name, bases, cls_dict):
            adder_func(cls)

    class BoundTemplate(Template):
        __metaclass__ = BoundTemplateMeta

    return BoundTemplate

def register(collection):
    def _register(func):
        collection[func.__name__] = func
        return func
    return _register


# Utils

def extends(func):
    def _decorator(wrapped_func):
        @contextlib.wraps(wrapped_func)
        def _inner(*args, **kwargs):
            return func(wrapped_func(*args, **kwargs))
        return _inner
    return _decorator
