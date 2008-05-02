# -*- coding: utf-8 -*-

from sqlalchemy import MetaData
from sqlalchemy.orm import create_session, scoped_session

from werkzeug import Local, LocalManager, Response
from werkzeug.wrappers import BaseResponse
from werkzeug.routing import Map, Rule

from templating import render_template

from picard.utils import simple_decorator

local = Local()
local_manager = LocalManager([local])
application = local('application')

metadata = MetaData()
session = scoped_session(lambda: create_session(application.database_engine,
                         transactional=True), local_manager.get_ident)

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

