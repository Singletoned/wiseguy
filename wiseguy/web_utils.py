# -*- coding: utf-8 -*-

from functools import wraps
import uuid
import os

import werkzeug as wz
try:
    import validino
    _validator_error = validino.Invalid
except ImportError:
    _validator_error = None

try:
    import jinja2
except ImportError:
    pass

try:
    import path
except ImportError:
    pass

try:
    import jade
except ImportError:
    pass

from wiseguy import utils


class TemplateNotFound(Exception):
    pass

def wsgi_wrapper(app, request_class=wz.Request):
    def application(environ, start_response):
        req = request_class(environ)
        res = app(req)
        res = res(environ, start_response)
        return res
    return application

def _do_dispatch(app, req):
    try:
        rule, kwargs = req.map_adapter.match(return_rule=True)
        if kwargs.has_key('path_info'):
            path_info = kwargs.pop('path_info')
            if not path_info.startswith("/"):
                path_info = "/" + path_info
            while path_info != req.environ['PATH_INFO']:
                popped = wz.wsgi.pop_path_info(req.environ)
                assert popped
        else:
            while req.environ['PATH_INFO']:
                wz.wsgi.pop_path_info(req.environ)
        endpoint = app.url_map.views[rule.endpoint]
        res = endpoint(req, **kwargs)
    except wz.exceptions.HTTPException, e:
        res = e.get_response(req.environ)
    return res

class BaseApp(object):
    def __init__(self, config, url_map, env):
        self.config = config
        self.env = env
        self.mountpoint = wz.Href(config.get('mountpoint', '/'))
        self.env.globals.update(
            dict(url=self.mountpoint))
        self.url_map = make_url_map(
            self.mountpoint(),
            url_map)

    def __call__(self, req):
        req.app = self
        req.map_adapter = self.url_map.bind_to_environ(req.environ)
        req.url_for = req.map_adapter.build
        res = _do_dispatch(self, req)
        if not isinstance(res, wz.BaseResponse):
            template_name, mimetype, values = res
            values = dict(request=req, **values)
            res = self.env.get_response(template_name, values, mimetype)
        return res

    def wsgi(self, request_class=wz.Request):
        return wsgi_wrapper(self, request_class)

class JinjaEnv(object):
    def __init__(self, env):
        self.env = env
        self.globals = env.globals

    def update_globals(self, context):
        self.env.globals.update(context)

    def render(self, template_name, context):
        try:
            template = self.env.get_template(template_name)
        except jinja2.TemplateNotFound:
            raise TemplateNotFound()
        return template.render(context)

    def get_response(self, template_name, context, mimetype="text/html"):
        body = self.render(template_name, context)
        res = wz.Response(body, mimetype=mimetype)
        return res

    def from_string(self, text):
        return self.env.from_string(text)

class LxmlEnv(object):
    def __init__(self, env, global_context=None):
        self.env = env
        if not global_context:
            global_context = dict()
        self.globals = global_context

    def update_globals(self, context):
        self.globals.update(context)

    def render(self, template_name, context):
        local_context = dict(self.globals)
        local_context.update(context)
        try:
            template = getattr(self.env, template_name)
        except AttributeError:
            raise TemplateNotFound()
        element = template(local_context)
        html = element.to_string()
        return html

    def get_response(self, template_name, context, mimetype="text/html"):
        body = self.render(template_name, context)
        res = wz.Response(body, mimetype=mimetype)
        return res

class JadeEnv(object):
    def __init__(self, directory, global_context=None):
        self.directory = path.path(directory)
        if global_context:
            self.globals = dict(global_context)
        else:
            self.globals = dict()
        self.globals['loader'] = self._loader

    def _loader(self, filename, context):
        f = self.directory / filename
        src = f.text()
        data = jade.generate_data(src)
        elements = jade.generate_elements(data, context=context)
        return elements

    def update_globals(self, context):
        self.globals.update(context)

    def render(self, template_name, context=None):
        local_context = dict(self.globals)
        if context:
            local_context.update(context)
        f = self.directory.child("%s.jade"%template_name)
        if not f.exists():
            raise TemplateNotFound()
        text = f.text()
        html = jade.to_html(text, context=local_context)
        return html

    def get_response(self, template_name, context, mimetype="text/html"):
        body = self.render(template_name, context)
        res = wz.Response(body, mimetype=mimetype)
        return res


class CascadingEnv(object):
    def __init__(self, *args):
        self.envs = args
        self.globals = dict()

    def update_globals(self, context):
        for env in self.envs:
            env.update_globals(context)

    def render(self, template_name, context=None):
        for env in self.envs:
            try:
                return env.render(template_name, context)
            except TemplateNotFound:
                pass
        raise TemplateNotFound()

    def get_response(self, template_name, context=None, mimetype="text/html"):
        for env in self.envs:
            try:
                return env.get_response(template_name, context, mimetype)
            except TemplateNotFound:
                pass
        raise TemplateNotFound()


def make_url_map(mountpoint, sub_url_map):
    url_map = UrlMap([
        wz.routing.Submount(
            mountpoint,
            sub_url_map.iter_rules())],
        views=sub_url_map.views,
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


class UrlMap(wz.routing.Map):
    def __init__(self, rules=None, views=None, *args, **kwargs):
        if not views:
            views = dict()
        self.views = views
        super(UrlMap, self).__init__(rules, *args, **kwargs)

    def expose(self, rule, methods=['GET'], **kw):
        def decorate(func):
            if not kw.has_key('endpoint'):
                if func.__name__ == "<lambda>":
                    endpoint = repr(func)
                else:
                    endpoint = func.__name__
                kw['endpoint'] = endpoint
            else:
                endpoint = kw['endpoint']
            self.views[endpoint] = func
            self.add(wz.routing.Rule(rule, methods=methods, **kw))
            return func
        return decorate

    def expose_submount(self, path):
        def decorate(f):
            self.views.update(f.url_map.views)
            self.add(
                wz.routing.Submount(
                    path,
                    f.url_map.iter_rules()))
            return f
        return decorate

    def add_subapp(self, subapp, path, prefix):
        self.views.update(dict([("%s.%s"%(prefix, k),v) for k,v in subapp.url_map.views.iteritems()]))
        self.add(
            wz.routing.EndpointPrefix(
                prefix+".",
                [wz.routing.Submount(path, subapp.url_map.iter_rules())]))

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

class Controller(object):
    def __call__(self, request):
        request.map_adapter =self.url_map.bind_to_environ(request.environ)
        res = _do_dispatch(self, request)
        return res

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
    def __new__(cls, request, **kwargs):
        if request.method == 'GET':
            return cls.GET(request, **kwargs)
        elif request.method == 'POST':
            data = utils.flatten_dict(
                request.form.to_dict(flat=False))
            try:
                return cls.POST(request, data=data, **kwargs)
            except _validator_error, e:
                errors = e.unpack_errors()
                return cls.GET(request, data=data, errors=errors, **kwargs)


def render_widget(widget):
    import lxml.html
    return lxml.html.tostring(widget)
