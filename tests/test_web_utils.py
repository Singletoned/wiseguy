# -*- coding: utf-8 -*-

import unittest
import os
import sys
import contextlib

import lxml.html
import werkzeug as wz
import werkzeug.test
import jinja2 as j2
import validino as v
import jade

import path

from wiseguy import web_utils as wu, utils
import wiseguy.html

@contextlib.contextmanager
def raises(error):
    try:
        yield
        raise Exception("%s not raised"%error)
    except error:
        pass
    except:
        (exc_type, exc_value, traceback) =  sys.exc_info()
        raise Exception("%s raised instead of %s" % (repr(exc_value), error))

var_dir = os.path.join(os.path.dirname(__file__), 'var')

def test_do_dispatch():
    url_map = wu.UrlMap()
    url_map.expose('/foo/bar')(lambda r: ("Foo Bar", r))
    url_map.expose('/foo/<path:path_info>')(lambda r: ("Foo Bar Baz", r))
    url_map.expose('/foo/flibble/<path:path_info>')(lambda r: ("Foo Flibble Wibble Dibble", r))
    app = utils.MockObject(url_map=url_map)

    req = wz.Request.from_values(path="/foo/bar")
    req.map_adapter = url_map.bind_to_environ(req.environ)
    (res, r) = wu._do_dispatch(app, req)
    assert res == "Foo Bar"
    assert r.environ["SCRIPT_NAME"] == "/foo/bar"
    assert r.environ["PATH_INFO"] == ""

    req = wz.Request.from_values(path="/foo/bar/baz")
    req.map_adapter = url_map.bind_to_environ(req.environ)
    (res, r) = wu._do_dispatch(app, req)
    assert res == "Foo Bar Baz"
    assert r.environ["SCRIPT_NAME"] == "/foo"
    assert r.environ["PATH_INFO"] == "/bar/baz"

    req = wz.Request.from_values(path="/foo/flibble/wibble/dibble")
    req.map_adapter = url_map.bind_to_environ(req.environ)
    (res, r) = wu._do_dispatch(app, req)
    assert res == "Foo Flibble Wibble Dibble"
    assert r.environ["SCRIPT_NAME"] == "/foo/flibble"
    assert r.environ["PATH_INFO"] == "/wibble/dibble"

def test_base_app():
    class TestRequest(wz.BaseRequest):
        def __init__(self, environ, **kwargs):
            super(self.__class__, self).__init__(environ)
            self.url = wz.Href("/submount")

        def __repr__(self):
            return "<TestRequest>"

    class OtherTestRequest(wz.BaseRequest):
        def __repr__(self):
            return "<OtherTestRequest>"

    um = wu.UrlMap()
    um.expose('/')(lambda r: wz.Response("Index"))
    um.expose('/foo')(lambda r: wz.Response("Foo Page"))
    um.expose('/bar')(lambda r: ('bar', 'text/html', {'bar_var': "flumble"}))
    um.expose('/jinja')(lambda r: wu.JinjaResponse('bar', {'bar_var': "bam"}))
    um.expose('/wrong')(lambda request: wz.redirect(request.url('/baz')))
    um.expose('/config')(lambda request: wz.Response(request.app.config.mountpoint))
    um.expose('/req')(lambda r: wz.Response(str(r)))

    renderer = wu.JinjaRenderer(
        j2.Environment(
            loader=j2.DictLoader(dict(bar="Bar Page {{bar_var}}")),
            extensions=['jinja2.ext.i18n']))

    app = wu.BaseApp(
        config=dict(mountpoint=u"/submount"),
        url_map=um,
        renderer=renderer,
        request_class=OtherTestRequest)
    wsgi_app = app.wsgi(request_class=TestRequest)
    other_wsgi_app = app.wsgi()

    response = wsgi_app(
        environ=wz.test.create_environ('/submount/req'),
        start_response=lambda status, headers: (status, headers))
    response = list(response)
    assert response == ["<TestRequest>"]

    response = other_wsgi_app(
        environ=wz.test.create_environ('/submount/req'),
        start_response=lambda status, headers: (status, headers))
    response = list(response)
    assert response == ["<OtherTestRequest>"]

    assert app.mountpoint() == u"/submount"
    assert app.mountpoint(u"bar") == u"/submount/bar"

    assert app.config.mountpoint == u"/submount"
    assert 'url' in app.renderer.globals

    for rule in app.url_map.iter_rules():
        assert rule.rule.startswith('/submount')

    environ = wz.test.create_environ('/submount/')
    test_request = TestRequest(environ)
    response = app(test_request, "foo", "bar", dict(a=1, b=2))
    assert response.data == "Index"

    environ = wz.test.create_environ('/submount/')
    response = wsgi_app(environ, lambda s, h: s)
    assert list(response) == ["Index"]

    environ = wz.test.create_environ('/submount')
    response = wsgi_app(environ, lambda s, h: s)
    response = list(response)[0]
    assert "Redirecting..." in response
    assert "/submount/" in response

    environ = wz.test.create_environ('/submount/foo')
    response = wsgi_app(environ, lambda s, h: s)
    assert list(response) == ["Foo Page"]

    environ = wz.test.create_environ('/submount/bar')
    response = wsgi_app(environ, lambda s, h: s)
    assert list(response) == ["Bar Page flumble"]

    environ = wz.test.create_environ('/submount/config')
    response = wsgi_app(environ, lambda s, h: s)
    assert list(response) == ["/submount"]

    environ = wz.test.create_environ('/submount/wrong')
    response = wsgi_app(environ, lambda s, h: s)
    response = list(response)[0]
    assert "Redirecting..." in response
    assert "/submount/baz" in response

    environ = wz.test.create_environ('/submount/jinja')
    response = wsgi_app(environ, lambda s, h: s)
    assert list(response) == ["Bar Page bam"]


def test_base_app_minimal():
    url_map = wu.UrlMap()
    renderer = j2.Environment()
    application = wu.BaseApp(
        config=dict(),
        url_map=url_map,
        renderer=renderer)


def test_base_app_config():
    url_map = wu.UrlMap()
    renderer = j2.Environment()
    application = wu.BaseApp(
        config=dict(foo=1, bar=2),
        url_map=url_map,
        renderer=renderer)
    assert application.config.foo == 1
    assert application.config.bar == 2


def test_base_app_name():
    url_map = wu.UrlMap()
    renderer = j2.Environment()
    application = wu.BaseApp(
        config=dict(),
        url_map=url_map,
        renderer=renderer,
        name="Mr Base App")
    assert application.name == "Mr Base App"
    assert repr(application) == "<BaseApp Mr Base App>"


def test_middlewares():
    url_map = wu.UrlMap()
    renderer = j2.Environment()
    application = wu.BaseApp(
        config=dict(),
        url_map=url_map,
        renderer=renderer,
        middlewares=[lambda app: "foo"])
    wsgi_app = application.wsgi()
    assert wsgi_app == "foo"


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


def test_JinjaResponse():
    renderer = wu.JinjaRenderer(
        j2.Environment(
            loader=j2.DictLoader(
                dict(foo="Foo Page {{bar}} {{a}}"))),
        context=dict(a=1, b=2))
    response = wu.JinjaResponse(
        "foo",
        {'bar': "baz"})
    assert response.data == ""
    returned_response = response.render(renderer)
    assert response.data == "Foo Page baz 1"
    assert returned_response == response


def test_JinjaRenderer():
    renderer = wu.JinjaRenderer(
        j2.Environment(
            loader=j2.DictLoader(
                dict(
                    bar="Foo Page {{foo_var}}",
                    flam="Flam Page {{wangle}}",
                    bangle="{{a}}, {{b}}"))),
        context=dict(a=1, b=2))

    html = renderer.render("bangle", {})
    assert html == "1, 2"

    html = renderer.render("bar", dict(foo_var="flangit"))
    assert html == "Foo Page flangit"

    response = renderer.get_response("bar", dict(foo_var="flibble"), "text/html")
    assert response.data == "Foo Page flibble"

    assert renderer.from_string("foo").render() == "foo"

    with raises(wu.TemplateNotFound):
        html = renderer.render("blanger", dict(blim="blam"))

    renderer.update_globals(dict(wangle="wotsit"))
    html = renderer.render("flam", dict())
    assert html == "Flam Page wotsit"

def test_LxmlRenderer():
    renderer = wu.LxmlRenderer(
            utils.MockObject(
                bar=lambda context: jade.jade("div Foo Page %s"%context['foo_var']),
                flam=lambda context: jade.jade("div Flam Page %s"%context['wangle']),))

    html = renderer.render("bar", dict(foo_var="flangit")).strip()
    assert html == "<div>Foo Page flangit</div>"

    response = renderer.get_response("bar", dict(foo_var="flibble"), "text/html")
    assert response.data.strip() == "<div>Foo Page flibble</div>"

    with raises(wu.TemplateNotFound):
        html = renderer.render("foo", dict(blim="blam")).strip()

    renderer.update_globals(dict(wangle="wotsit"))
    html = renderer.render("flam", dict()).strip()
    assert html == "<div>Flam Page wotsit</div>"

def test_JadeRenderer():
    with path.create_temp_dir() as d:
        layout_content = """
html
  body
    block body
    div(class={{baz_var}})"""
        index_content = """
extends layout.jade

append body
  div: p: a.foo"""
        foo_content = """
extends layout.jade

append body
  div= foo_var
  div(class={{bar_var}})
"""
        flam_content = """div= wangle"""
        d.child('layout.jade').write_text(layout_content)
        d.child('index.jade').write_text(index_content)
        d.child('foo.jade').write_text(foo_content)
        d.child('flam.jade').write_text(flam_content)
        renderer = wu.JadeRenderer(d, dict(bar_var="bibble", baz_var="baz"))

        html = renderer.render("index").strip()
        expected = '''
<html><body>
<div><p><a class="foo"></a></p></div>
<div class="baz"></div>
</body></html>'''.strip()
        assert expected == html

        response = renderer.get_response("foo", dict(foo_var="flibble"), "text/html")
        expected = '''
<html><body>
<div>flibble</div>
<div class="bibble"></div>
<div class="baz"></div>
</body></html>'''.strip()
        assert response.data.strip() == expected

        with raises(wu.TemplateNotFound):
            html = renderer.render("blooble").strip()

        renderer.update_globals(dict(wangle="wotsit"))
        html = renderer.render("flam", dict()).strip()
        assert html == "<div>wotsit</div>"

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

    class FooClass(object):
        def __call__(self, request):
            return "This is a callable object"

    url_map.expose(u"/test_callable", endpoint="callable")(FooClass())

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
    check_url(u"/test_callable", u"GET", '', u"This is a callable object")


def test_UrlMap_expose_subapp():
    url_map = wu.UrlMap()

    application = wu.BaseApp(
        config=dict(),
        url_map=wu.UrlMap(),
        renderer=j2.Environment(),
        name="Mr Testy")

    url_map.expose_subapp('/subapp', application)

    assert "<BaseApp Mr Testy>" in url_map.views
    rules = list(url_map.iter_rules())
    assert len(rules) == 2
    for rule in rules:
        assert rule.methods == None
    assert rules[0].rule == "/subapp"
    assert rules[1].rule == "/subapp<path:path_info>"


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

    renderer = j2.Environment(loader=j2.DictLoader(templates))

    render = wu.create_render(renderer)

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


def test_CascadingRenderer():
    with path.create_temp_dir() as d:
        d.child('bar3.jade').write_text("""div Jade Page\n  !=" "+foo_var""")

        renderer = wu.CascadingRenderer(
            wu.LxmlRenderer(
                utils.MockObject(
                    bar1=lambda context: jade.jade(
                        "div Lxml Page %s"%context['foo_var']))),
            wu.JinjaRenderer(
                j2.Environment(
                    loader=j2.DictLoader(
                        dict(
                            bar2="<div>Jinja Page {{foo_var}}</div>",
                            flam="<div>Flam Page {{wangle}}</div>")))),
            wu.JadeRenderer(d, dict()))

        expected = "<div>Lxml Page flam</div>"
        result = renderer.render("bar1", dict(foo_var="flam")).strip()
        assert result == expected
        result = renderer.get_response("bar1", dict(foo_var="flam"))
        assert result.data.strip() == expected

        expected = "<div>Jinja Page flom</div>"
        result = renderer.render("bar2", dict(foo_var="flom")).strip()
        assert result == expected
        result = renderer.get_response("bar2", dict(foo_var="flom"), mimetype="blah")
        assert result.data.strip() == expected
        assert result.mimetype == "blah"

        expected = "<div>Jade Page flim</div>"
        result = renderer.render("bar3", dict(foo_var="flim")).strip()
        assert result == expected
        result = renderer.get_response("bar3", dict(foo_var="flim"))
        assert result.data.strip() == expected

        with raises(wu.TemplateNotFound):
            result = renderer.render("flib", dict())

        with raises(wu.TemplateNotFound):
            result = renderer.get_response("flib", dict())

        renderer.update_globals(dict(wangle="wotsit"))
        html = renderer.render("flam", dict()).strip()
        assert html == "<div>Flam Page wotsit</div>"


def test_Controller():
    class FooController(wu.Controller):
        url_map = wu.UrlMap()

        @url_map.expose(u"/")
        def index(request):
            assert request.foo
            return "This is the Index"

        @url_map.expose(u"/bar")
        def bar(request):
            assert request.foo
            return "This is the bar controller"

    foo_controller = FooController()

    req = wz.Request.from_values(path="/", base_url="http://example.com/foo")
    req.foo = True

    res = foo_controller(req)
    assert res == "This is the Index"

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

def test_url_map_add_subapp():
    sub_url_map = wu.UrlMap()

    @sub_url_map.expose("/index")
    def index(request):
        pass

    sub_app = wu.BaseApp(
        config=dict(),
        url_map=sub_url_map,
        renderer=wu.CascadingRenderer())

    url_map = wu.UrlMap()
    url_map.add_subapp(sub_app, "/sub", "sub")

    assert url_map.views.has_key("sub.index")
    assert url_map.views["sub.index"] == index


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
