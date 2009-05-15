import werkzeug


def simple_decorator(decorator):
    """This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied.
    >>> @simple_decorator
    ... def test_func():
    ...     "This is the docstring of test_func"
    ...     print "functon was called"
    ...     
    >>> test_func.__doc__
    'This is the docstring of test_func'
    >>> test_func.__name__
    'test_func'
    """
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
            url_map.add(werkzeug.routing.Rule(rule, methods=methods, **kw))
            return f
        return decorate
    return expose


def create_render(env):
    def render(template_name, mimetype='text/html'):
        @simple_decorator
        def decorate(f):
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

