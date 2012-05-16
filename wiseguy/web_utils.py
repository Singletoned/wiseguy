# -*- coding: utf-8 -*-

from functools import wraps
import uuid
import os

import werkzeug as wz
import validino
import jinja2

from wiseguy import form_fields, utils


class BaseApp(object):
    def __init__(self, config, url_map, env, request_class=wz.Request):
        self.config = config
        self.env = env
        self.mountpoint = wz.Href(config.get('mountpoint', '/'))
        self._request_class = request_class
        self.env.globals.update(
            dict(url=self.mountpoint))
        self.url_map = wz.routing.Map([
            wz.routing.Submount(
                self.mountpoint(),
                url_map.iter_rules())])

    def __call__(self, environ, start_response):
        req = self._request_class(environ)
        req.app = self
        req.map_adapter = self.url_map.bind_to_environ(environ)
        try:
            endpoint, kwargs = req.map_adapter.match()
            res = endpoint(req, **kwargs)
            if not isinstance(res, wz.BaseResponse):
                template_name, mimetype, values = res
                values = dict(request=req, **values)
                body = self.env.get_template(template_name).render(values)
                res = wz.Response(body, mimetype=mimetype)
        except wz.exceptions.HTTPException, e:
            res = e
        res = res(environ, start_response)
        return wz.ClosingIterator(res)

def make_url_map(mountpoint, sub_url_map):
    url_map = wz.routing.Map([
        wz.routing.Submount(
            mountpoint,
            sub_url_map.iter_rules())],
        converters=sub_url_map.converters)
    return url_map


def render(template_name, mimetype="text/html"):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            values = func(*args, **kwargs)
            if isinstance(values, wz.BaseResponse):
                return values
            else:
                return (template_name, mimetype, values)
        return wrapper
    return decorate

def make_client_env(var_dir, client, extra_globals=None):
    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(
                os.path.join(
                    var_dir,
                    client,
                    "templates")),
            jinja2.FileSystemLoader(
                os.path.join(
                    var_dir,
                    "default",
                    "templates"))]),
        extensions=['jinja2.ext.i18n'])
    if extra_globals:
        env.globals.update(extra_globals)
    return env

def create_expose(url_map):
    def expose(rule, methods=['GET'], **kw):
        def decorate(f):
            kw['endpoint'] = f
            url_map.add(wz.routing.Rule(rule, methods=methods, **kw))
            return f
        return decorate
    return expose


class UrlMap(wz.routing.Map):
    def expose(self, rule, methods=['GET'], **kw):
        def decorate(f):
            kw['endpoint'] = f
            self.add(wz.routing.Rule(rule, methods=methods, **kw))
            return f
        return decorate

    def expose_submount(self, path):
        def decorate(f):
            self.add(
                wz.routing.Submount(
                    path,
                    f.url_map.iter_rules()))
            return f
        return decorate


class UUIDConverter(wz.routing.BaseConverter):
    def __init__(self, url_map):
        super(UUIDConverter, self).__init__(url_map)
        self.regex = '(?:[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})'

    def to_python(self, value):
        return str(uuid.UUID(value))

    def from_url(self, value):
        if isinstance(uuid.UUID, value):
            return value
        else:
            return uuid.UUID(value)


def create_env_and_render(loader_type, path, name):
    "Create a Jinja2 Environment and pass it to create_render"
    env = jinja2.Environment(
        loader=getattr(jinja2, loader_type)(path, name),
    )
    env.globals.update(dict(form_fields=form_fields))
    return create_render(env)

def create_render(env):
    "Create a render decorator that passes the return value of a function to the named template"
    def render(template_name, mimetype='text/html'):
        "Render the return value of the function in the named template, unless it is already a Response object"
        def decorate(f):
            @wraps(f)
            def func(*args, **kwargs):
                values = f(*args, **kwargs)
                try:
                    values.update({u'request':args[0]})
                except (TypeError, AttributeError):
                    return values
                body = env.get_template(template_name).render(values)
                return wz.Response(body, mimetype=mimetype)
            return func
        return decorate
    return render

def create_require(predicate, response_builder):
    u"""Create a decorator that requires ``predicate(request)`` to
    evaluate ``True`` before calling the decorated function. If the
    predicate evalutates ``False`` then ``response_builder`` is called
    with the original function, request and args and kwargs and
    returned.
    """
    def require(func):
        @wraps(func)
        def decorated(request, *args, **kwargs):
            if predicate(request):
                return func(request, *args, **kwargs)
            else:
                return response_builder(func, request, *args, **kwargs)
        return decorated
    return require


class Handler(object):
    def __new__(cls, _parent=None):
        handler = object.__new__(cls)
        handler._parent = _parent
        for k, v in cls.__dict__.items():
            if isinstance(v, type):
                if issubclass(v, Handler):
                    setattr(handler, k, v(_parent=handler))
        return handler


class FormHandler(object):
    _validator_error = validino.Invalid
    def __new__(cls, request, **kwargs):
        if request.method == 'GET':
            return cls.GET(request, **kwargs)
        elif request.method == 'POST':
            data = utils.flatten_dict(
                request.form.to_dict(flat=False))
            try:
                return cls.POST(request, data=data, **kwargs)
            except cls._validator_error, e:
                errors = e.unpack_errors()
                return cls.GET(request, data=data, errors=errors, **kwargs)


def render_widget(widget):
    import lxml.html
    return lxml.html.tostring(widget)
