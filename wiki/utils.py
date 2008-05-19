# -*- coding: utf-8 -*-

from peak.util.decorators import decorate_class

from werkzeug import Response
from werkzeug.wrappers import BaseResponse

from werkzeug.routing import Rule

from picard.utils import simple_decorator, create_expose

from templating import render_template

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

        