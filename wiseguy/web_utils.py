from functools import wraps

import werkzeug as wz
import validino
import jinja2

def create_expose(url_map):
    def expose(rule, methods=['GET'], **kw):
        def decorate(f):
            kw['endpoint'] = f
            url_map.add(wz.routing.Rule(rule, methods=methods, **kw))
            return f
        return decorate
    return expose

def create_env_and_render(loader_type, path, name):
    "Create a Jinja2 Environment and pass it to create_render"
    env = jinja2.Environment(
        loader=getattr(jinja2, loader_type)(path, name),
    )
    return create_render(env)

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
                return wz.Response(body, mimetype=mimetype)
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


class FormHandler(object):
    _validator_error = validino.Invalid
    def __new__(cls, request, **kwargs):
        if request.method == 'GET':
            return cls.GET(request, **kwargs)
        elif request.method == 'POST':
            data = request.form.to_dict()
            try:
                return cls.POST(request, data=data, **kwargs)
            except cls._validator_error, e:
                errors = e.unpack_errors()
                return cls.GET(request, data=data, errors=errors, **kwargs)
