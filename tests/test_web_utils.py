import werkzeug as wz
import jinja2 as j2
import validino as v

from wiseguy import web_utils as wu, utils


def test_create_expose():
    url_map = wz.routing.Map()
    expose = wu.create_expose(url_map)

    @expose(u"/test")
    def get(param1):
        u"This is the get function"
        return "GET " + param1

    assert get.__doc__ == u"This is the get function"
    assert get.__name__ == "get"

    @expose(u"/test", methods=[u"POST"])
    def post(param1):
        u"This is the post function"
        return "POST " + param1

    assert post.__doc__ == u"This is the post function"
    assert post.__name__ == "post"

    @expose(u"/test_both", methods=[u"GET", "POST"])
    def post_and_get(param1):
        u"This is the post_and_get function"
        return "GET POST " + param1

    assert post_and_get.__doc__ == u"This is the post_and_get function"
    assert post_and_get.__name__ == "post_and_get"

    def check_url(_url, _method, _endpoint, _response):
        urls = url_map.bind_to_environ(utils.MockEnv(_url, _method))
        endpoint, kwargs = urls.match()
        assert endpoint == _endpoint, u"Should have chosen the correct function"
        res = endpoint("p1", **kwargs)
        assert res == _response

    check_url(u"/test", u"GET", get, u"GET p1")
    check_url(u"/test", u"POST", post, u"POST p1")
    check_url(u"/test_both", u"GET", post_and_get, u"GET POST p1")
    check_url(u"/test_both", u"POST", post_and_get, u"GET POST p1")


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


def test_FormHandler():
    class FooForm(wu.FormHandler):
        @staticmethod
        def GET(request, data=None, errors=None):
            return ("GET", data)

        @staticmethod
        def POST(request, data=None):
            s = v.Schema(
                dict(foo=v.integer())
                )
            data = s(data)
            return ("POST", data)

    request = utils.MockObject(method='GET')
    result = FooForm(request)
    expected = ("GET", None)
    assert result == expected

    form = utils.MockObject(to_dict=lambda: dict(foo=1))
    request = utils.MockObject(method='POST', form=form)
    result = FooForm(request)
    expected = ("POST", dict(foo=1))
    assert result == expected

    form = utils.MockObject(to_dict=lambda: dict(foo="abc"))
    request = utils.MockObject(method='POST', form=form)
    result = FooForm(request)
    expected = ("GET", dict(foo="abc"))
    assert result == expected
