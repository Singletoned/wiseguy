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

