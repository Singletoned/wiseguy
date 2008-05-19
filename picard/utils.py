# -*- coding: utf-8 -*-

from werkzeug import Response
from werkzeug.routing import Rule

from jinja import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

def render_template(template_name, *args, **kwargs):
    """Gets a template and renders it"""
    return env.get_template('%s.html' % template_name).render(kwargs)

def render(template_name, mimetype='text/html'):
    @simple_decorator
    def decorate(f):
        def func(*args, **kwargs):
            values = f(*args, **kwargs)
            try:
                return Response(render_template(template_name, **values), mimetype=mimetype)
            except TypeError:
                return values
        return func
    return decorate

def simple_decorator(decorator):
    """This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied."""
    def new_decorator(f):
        g = decorator(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

def create_expose(url_map):
    def expose(rule, methods=['GET'], **kw):
        @simple_decorator
        def decorate(f):
            kw['endpoint'] = f.__name__
            url_map.add(Rule(rule, methods=methods, **kw))
            return f
        return decorate
    return expose


def with_page_from(var):
    @simple_decorator
    def decorate(f):
        def func(*args, **kwargs):
            page = getattr(args[0].models.Page, 'get_by_'+var)(kwargs.pop('address'))
            if not page:
                raise NotFound
            kwargs['page'] = page
            return f(*args, **kwargs)
        return func
    return decorate

# 
# def expose_class(rule, methods=['GET'], **kw):
#     def decorate(f):
#         kw['endpoint'] = f.__name__
#         url_map.add(Rule(rule, methods=methods, **kw))
#         return f
#     decorate_class(decorate)
# 
# def render_class(template_name, mimetype='text/html'):
#     def decorate(f):
#         def func(request, *args, **kwargs):
#             values = getattr(f, request.method.upper())(request, *args, **kwargs)
#             try:
#                 return Response(render_template(template_name, **values), mimetype=mimetype)
#             except TypeError:
#                 return values
#         return func
#     decorate_class(decorate)
# 
