# -*- coding: utf-8 -*-

from sqlalchemy import MetaData
from sqlalchemy.orm import create_session, scoped_session

from werkzeug import Local, LocalManager, Response
from werkzeug.wrappers import BaseResponse
from werkzeug.routing import Map, Rule

from templating import render_template

local = Local()
local_manager = LocalManager([local])
application = local('application')

metadata = MetaData()
session = scoped_session(lambda: create_session(application.database_engine,
                         transactional=True), local_manager.get_ident)

url_map = Map()

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

