# -*- coding: utf-8 -*-

import collections, copy, functools, contextlib

import lxml.html

class Transform(object):
    def __init__(self, keys, transform):
        if isinstance(keys, basestring):
            self.keys = set([keys])
        else:
            self.keys = set(keys)
        self.transform = transform
        self.applied = False
        self.context = dict()

    def __repr__(self):
        return "<Transform %s>" % self.keys

    def apply(self, context):
        for key in list(self.keys):
            if key in context:
                self.context[key] = context[key]
                self.keys.remove(key)
        if not self.keys:
            self.applied = True

class TemplateMeta(type):
    applied_transforms = []

    def _pop_keys(self, key, context):
        kwargs = dict([(k, context[k]) for k in key])
        while self.transforms[key]:
            transform = self.transforms[key].pop(0)
            transform(template=self.template, **kwargs)

    def apply(self, context):
        for transform in list(self.transforms):
            transform.apply(context)
            if transform.applied:
                transform.transform(template=self.template, **transform.context)
                self.transforms.remove(transform)
                self.applied_transforms.append(transform)

    def copy(self):
        return TemplateMeta(
            'Template',
            (Template,),
            dict(
                template=copy.deepcopy(self.template),
                transforms=copy.deepcopy(self.transforms)))

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
        self.transforms = []
        for value in cls_dict.itervalues():
            if hasattr(value, 'transforms'):
                self.transforms.extend(value.transforms)

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

def extends(template):
    def _decorator(wrapped_template):
        new_template = template.copy()
        new_template.apply(
            wrapped_template(dict()))
        new_template.transforms.extend(
            wrapped_template.transforms)
        return new_template
    return _decorator
