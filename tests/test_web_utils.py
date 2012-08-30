# -*- coding: utf-8 -*-

import unittest
import os

import lxml.html
import werkzeug as wz
import werkzeug.test
import jinja2 as j2
import validino as v

from wiseguy import web_utils as wu, utils


var_dir = os.path.join(os.path.dirname(__file__), 'var')


def test_base_app():
    class TestRequest(wz.BaseRequest):
        def __init__(self, environ, **kwargs):
            super(self.__class__, self).__init__(environ)
            self.url = wz.Href("/submount")

    url_map = wu.UrlMap()
    url_map.expose('/')(lambda r: wz.Response("Index"))
    url_map.expose('/foo')(lambda r: wz.Response("Foo Page"))
    url_map.expose('/bar')(lambda r: ('bar', 'text/html', {'bar_var': "flumble"}))
    url_map.expose('/wrong')(lambda request: wz.redirect(request.url('/baz')))
    url_map.expose('/config')(lambda request: wz.Response(request.app.config['mountpoint']))

    env = wu.JinjaEnv(
        j2.Environment(
            loader=j2.DictLoader(dict(bar="Bar Page {{bar_var}}")),
            extensions=['jinja2.ext.i18n']))

    app = wu.BaseApp(
        config=dict(mountpoint=u"/submount"),
        url_map=url_map,
        env=env,
        request_class=TestRequest)

    assert app.mountpoint() == u"/submount"
    assert app.mountpoint(u"bar") == u"/submount/bar"

    assert app.config['mountpoint'] == u"/submount"
    assert 'url' in app.env.globals

    for rule in app.url_map.iter_rules():
        assert rule.rule.startswith('/submount')

    environ = wz.test.create_environ('/submount/')
    response = app(environ, lambda s, h: s)
    assert list(response) == ["Index"]

    environ = wz.test.create_environ('/submount')
    response = app(environ, lambda s, h: s)
    response = list(response)[0]
    assert "Redirecting..." in response
    assert "/submount/" in response

    environ = wz.test.create_environ('/submount/foo')
    response = app(environ, lambda s, h: s)
    assert list(response) == ["Foo Page"]

    environ = wz.test.create_environ('/submount/bar')
    response = app(environ, lambda s, h: s)
    assert list(response) == ["Bar Page flumble"]

    environ = wz.test.create_environ('/submount/config')
    response = app(environ, lambda s, h: s)
    assert list(response) == ["/submount"]

    environ = wz.test.create_environ('/submount/wrong')
    response = app(environ, lambda s, h: s)
    response = list(response)[0]
    assert "Redirecting..." in response
    assert "/submount/baz" in response

def test_base_app_minimal():
    url_map = wu.UrlMap()
    env = j2.Environment()
    application = wu.BaseApp(
        config=dict(),
        url_map=url_map,
        env=env)

def test_make_url_map():
    flibble_conv = lambda: "flibble"
    sub_url_map = wu.UrlMap(
        [
            wz.routing.Rule('/', endpoint="."),
            wz.routing.Rule('/foo', endpoint="foo")],
        converters=dict(flibble=flibble_conv))
    url_map = wu.make_url_map("/blammo", sub_url_map)
    adapter = url_map.bind('example.com')
    assert adapter.match('/blammo/') == (".", {})
    assert adapter.match('/blammo/foo') == ("foo", {})
    assert url_map.converters['flibble'] == flibble_conv

def test_JinjaEnv():
    env = wu.JinjaEnv(
        j2.Environment(
            loader=j2.DictLoader(dict(bar="Foo Page {{foo_var}}"))))

    html = env.render("bar", dict(foo_var="flangit"))
    assert html == "Foo Page flangit"

    response = env.get_response("bar", dict(foo_var="flibble"), "text/html")
    assert response.data == "Foo Page flibble"

def test_LxmlEnv():
    env = wu.LxmlEnv(
            utils.MockObject(
                bar=lambda context: "Foo Page %s"%context['foo_var']))

    html = env.render("bar", dict(foo_var="flangit"))
    assert html == "Foo Page flangit"

    response = env.get_response("bar", dict(foo_var="flibble"), "text/html")
    assert response.data == "Foo Page flibble"

def test_render():
    foo = lambda x: x
    mock_request = object()
    wrapped_foo = wu.render("bar.html", "text/flibble")(foo)
    template_name, mimetype, values = wrapped_foo(mock_request)
    assert template_name == "bar.html"
    assert mimetype == "text/flibble"
    assert values == mock_request

    test_response = wz.BaseResponse("")
    foo = lambda x: test_response
    mock_request = object()
    wrapped_foo = wu.render("bar.html", "text/flibble")(foo)
    response = wrapped_foo(mock_request)
    assert response is test_response

def test_UrlMap():
    url_map = wu.UrlMap()

    @url_map.expose(u"/test")
    def get(param1):
        u"This is the get function"
        return "GET " + param1

    assert get.__doc__ == u"This is the get function"
    assert get.__name__ == "get"

    @url_map.expose(u"/test", methods=[u"POST"])
    def post(param1):
        u"This is the post function"
        return "POST " + param1

    assert post.__doc__ == u"This is the post function"
    assert post.__name__ == "post"

    @url_map.expose(u"/test_both", methods=[u"GET", "POST"])
    def post_and_get(param1):
        u"This is the post_and_get function"
        return "GET POST " + param1

    assert post_and_get.__doc__ == u"This is the post_and_get function"
    assert post_and_get.__name__ == "post_and_get"

    lambda_func = url_map.expose('/test_lambda')(lambda request: "This is a lambda")
    assert lambda_func.__name__ == "<lambda>"

    def check_url(_url, _method, _endpoint_name, _response):
        urls = url_map.bind_to_environ(utils.MockEnv(_url, _method))
        endpoint_name, kwargs = urls.match()
        if _endpoint_name:
            assert endpoint_name == _endpoint_name, u"Should have chosen the correct function"
        endpoint = url_map.views[endpoint_name]
        res = endpoint("p1", **kwargs)
        assert res == _response

    check_url(u"/test", u"GET", 'get', u"GET p1")
    check_url(u"/test", u"POST", 'post', u"POST p1")
    check_url(u"/test_both", u"GET", 'post_and_get', u"GET POST p1")
    check_url(u"/test_both", u"POST", 'post_and_get', u"GET POST p1")
    check_url(u"/test_lambda", u"GET", '', u"This is a lambda")


def test_UUIDConverter():
    url_map = wz.routing.Map([
        wz.routing.Rule("/<uuid:foo_id>", endpoint="foo")],
        converters={'uuid':wu.UUIDConverter})
    adapter = url_map.bind('example.com')
    result = adapter.match("/01234567-89AB-CDEF-0123-456789ABCDEF")
    expected = ("foo", {"foo_id": "01234567-89ab-cdef-0123-456789abcdef"})
    assert result == expected


def test_create_render():
    templates = {
        u'index': u"This is the index page.  Path: {{ request.path }}.  Greeting: {{ greeting }}",
        u'about': u"This is the about page.  Path: {{ request.path }}"
    }

    env = j2.Environment(loader=j2.DictLoader(templates))

    render = wu.create_render(env)

    @render(u"index")
    def index_page(req):
        return {u'greeting': "Hello"}

    @render(u"about")
    def about_page(req):
        return {}

    @render(u"contact")
    def contact(req):
        return wz.redirect(u"/other_page")

    req = wz.Request(utils.MockEnv(u"/", u"GET"))

    res = index_page(req)
    assert res.response[0] == "This is the index page.  Path: /.  Greeting: Hello"

    res = about_page(req)
    assert res.response[0] == "This is the about page.  Path: /"

    res = contact(req)
    assert u"Redirecting..." in res.response[0]
    assert u"/other_page" in res.response[0]


def test_make_client_env():
    def check_result(result):
        assert not "master template" in result
        assert "This is global" in result

    mrflibble_env = wu.make_client_env(
        var_dir=var_dir,
        client="mrflibble",
        extra_globals=dict(a_global_func=lambda:"This is global"))
    result = mrflibble_env.get_template("index.html").render()
    assert "Mr Flibble" in result
    assert not "default" in result
    check_result(result)

    result = mrflibble_env.get_template("page.html").render()
    assert "default page" in result
    assert not "flibble" in result
    check_result(result)

    ladywotsit_env = wu.make_client_env(
        var_dir=var_dir,
        client="ladywotsit",
        extra_globals=dict(a_global_func=lambda:"This is global"))
    result = ladywotsit_env.get_template("index.html").render()
    assert "default" in result
    assert not "Mr Flibble" in result
    check_result(result)

    result = ladywotsit_env.get_template("page.html").render()
    assert "default page" in result
    assert not "flibble" in result
    check_result(result)


class TestFormHandler(unittest.TestCase):
    class FooForm(wu.FormHandler):
        @staticmethod
        def GET(request, data=None, errors=None, item_id=None):
            return "This is GET with item_id: %s and data: %s and errors: %s" % (item_id, data, errors)

        @staticmethod
        def POST(request, data=None, item_id=None):
            if data == dict(do_raise=True):
                raise v.Invalid("You told me to raise")
            return "This is POST with item_id: %s and data: %s" % (item_id, data)

    def test_GET(self):
        class MockRequest(object):
            method = "GET"

        result = self.FooForm(MockRequest)
        expected = "This is GET with item_id: None and data: None and errors: None"
        assert result == expected

        result = self.FooForm(MockRequest, item_id="foo")
        expected = "This is GET with item_id: foo and data: None and errors: None"
        assert result == expected

    def test_POST(self):
        class MockRequest(object):
            method = "POST"
            form = utils.MockObject(
                to_dict=lambda flat: dict(foo="blam"))

        result = self.FooForm(MockRequest)
        expected = "This is POST with item_id: None and data: {'foo': 'blam'}"
        assert result == expected

    def test_POST_with_error(self):
        class MockRequest(object):
            method = "POST"
            form = utils.MockObject(
                to_dict=lambda flat: dict(do_raise=True))

        result = self.FooForm(MockRequest)
        expected = "This is GET with item_id: None and data: {'do_raise': True} and errors: {None: 'You told me to raise'}"
        assert result == expected

    def test_POST_with_nested_data(self):
        class MockRequest(object):
            method = "POST"
            form = utils.MockObject(
                to_dict=lambda flat: dict(flamble=[1,2,3], flooble=["flooble"]))

        result = self.FooForm(MockRequest)
        expected = "This is POST with item_id: None and data: {'flamble': [1, 2, 3], 'flooble': 'flooble'}"
        assert result == expected


def test_create_require():
    require_mod_2 = wu.create_require(
        lambda r: bool(r.value),
        response_builder=lambda r, f, *a, **k: (r, f, a, k))

    def foo(request, *args, **kwargs):
        return utils.MockObject(
            args=args,
            kwargs=kwargs)

    decorated_foo = require_mod_2(foo)

    passing_request = utils.MockObject(value=True)
    response = decorated_foo(passing_request, 1, 2, a=1, b=2)
    assert isinstance(response, utils.MockObject)
    assert response.args == (1, 2)
    assert response.kwargs == {'a': 1, 'b': 2}

    failing_request = utils.MockObject(value=False)
    func, request, args, kwargs = decorated_foo(failing_request, 1, 2, a=1, b=2)
    assert func == foo
    assert request == failing_request
    assert args == (1, 2)
    assert kwargs == {'a': 1, 'b': 2}


def test_render_widget():
    widget = lxml.html.fromstring("foo")
    result = wu.render_widget(widget)
    expected = "<p>foo</p>"
    assert result == expected

def test_url_map_submount():
    url_map = wu.UrlMap()

    @url_map.expose_submount('/foo')
    class FooController(object):
        url_map = wu.UrlMap()

        @url_map.expose("/flibble")
        def flibble_view():
            return "Hullo"

    environ = wz.test.create_environ('/flibble')
    endpoint_name, kwargs = FooController.url_map.bind_to_environ(environ).match()
    endpoint = url_map.views[endpoint_name]
    result = endpoint(**kwargs)
    assert result == "Hullo"

    environ = wz.test.create_environ('/foo/flibble')
    endpoint_name, kwargs = url_map.bind_to_environ(environ).match()
    endpoint = url_map.views[endpoint_name]
    result = endpoint(**kwargs)
    assert result == "Hullo"

    @url_map.expose_submount('')
    class BarController(object):
        url_map = wu.UrlMap()

        @url_map.expose("/flibble")
        def flibble_view():
            return "Hullo"

    environ = wz.test.create_environ('/flibble')
    endpoint_name, kwargs = url_map.bind_to_environ(environ).match()
    endpoint = url_map.views[endpoint_name]
    result = endpoint(**kwargs)
    assert result == "Hullo"

    @url_map.expose_submount('/flamble')
    class FlambleController(object):
        url_map = wu.UrlMap()

        @url_map.expose("/flibble")
        def flibble_view():
            return "Hullo"

    @url_map.expose_submount('/flooble')
    class FloobleController(FlambleController):
        pass

    environ = wz.test.create_environ('/flooble/flibble')
    endpoint_name, kwargs = url_map.bind_to_environ(environ).match()
    endpoint = url_map.views[endpoint_name]
    result = endpoint(**kwargs)
    assert result == "Hullo"


class test_Handler(unittest.TestCase):
    def test_simple(self):
        class FooHandler(wu.Handler):
            url_route = "/foo"

            def __call__(self):
                return "FOO!"

        foo_handler = FooHandler()

        assert foo_handler.url_route == "/foo"
        assert foo_handler() == "FOO!"

    def test_inheritance(self):
        class FooHandler(wu.Handler):
            url_route = "/foo"

            def __call__(self):
                return "FOO!"

        class BarHandler(wu.Handler):
            url_map = wu.UrlMap()
            foo = FooHandler

        bar_handler = BarHandler()
        assert isinstance(bar_handler.foo, FooHandler)
        assert bar_handler.foo._parent == bar_handler
