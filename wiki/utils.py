# -*- coding: utf-8 -*-

from peak.util.decorators import decorate_class

from werkzeug import Response
from werkzeug.wrappers import BaseResponse
from werkzeug.routing import Map, Rule

from picard.utils import simple_decorator

from templating import render_template

url_map = Map()

def expose(rule, methods=['GET'], **kw):
    @simple_decorator
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, methods=methods, **kw))
        return f
    return decorate

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

def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)

def expose_class(rule, methods=['GET'], **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, methods=methods, **kw))
        return f
    decorate_class(decorate)

def render_class(template_name, mimetype='text/html'):
    def decorate(f):
        def func(request, *args, **kwargs):
            values = getattr(f, request.method.upper())(request, *args, **kwargs)
            try:
                return Response(render_template(template_name, **values), mimetype=mimetype)
            except TypeError:
                return values
        return func
    decorate_class(decorate)

        