from functools import wraps

import werkzeug


def create_expose(url_map):
    def expose(rule, methods=['GET'], **kw):
        def decorate(f):
            kw['endpoint'] = f.__name__
            url_map.add(werkzeug.routing.Rule(rule, methods=methods, **kw))
            return f
        return decorate
    return expose


def create_render(env):
    def render(template_name, mimetype='text/html'):
        def decorate(f):
            @wraps(f)
            def func(*args, **kwargs):
                values = f(*args, **kwargs)
                try:
                    values.update({u'req':args[0]})
                except (TypeError, AttributeError):
                    return values
                body = env.get_template(template_name).render(values)
                return werkzeug.Response(body, mimetype=mimetype)
            return func
        return decorate
    return render


def create_require(predicate, template=None, response_builder=None, mimetype=u'text/html'):
    u"""
    Create a decorator that requires ``predicate(request)`` to evaluate
    ``True`` before calling the decorated function. If the predicate evalutates
    ``False`` then either ``response_builder`` is called with the request and returned, or ``template`` is rendered and returned.
    """
    assert template or response_builder, u"Must specify either a template or response_builder"
    assert not (template and response_builder), u"Must only specify one of template or response_builder"
    def require(func):
        @wraps(func)
        def decorated(request, *args, **kwargs):
            if predicate(request):
                return func(request, *args, **kwargs)
            elif response_builder:
                return response_builder(request)
            else:
                return Response(
                    template.render({u'request': request}),
                    mimetype=mimetype
                )
        return decorated
    return require


### Utils for Tests

def MockEnv(path, method):
    """Returns a simple WSGI environment.  Pretends to be a class.
    >>> env = MockEnv("/path", "POST")
    >>> env # doctest:+ELLIPSIS
    {'SERVER_PORT': '80', 'SERVER_PROTOCOL': 'HTTP/1.1', 'SCRIPT_NAME': '', 'wsgi.input': ...
    >>> env[u"PATH_INFO"]
    '/path'
    >>> env[u"REQUEST_METHOD"]
    'POST'
    """
    return werkzeug.EnvironBuilder(path=path, method=method).get_environ()

