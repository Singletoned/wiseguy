from werkzeug import EnvironBuilder
from werkzeug.routing import Map

from utils import create_expose, MockEnv


def test_create_expose():
    url_map = Map()
    expose = create_expose(url_map)

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

    _locals = locals()

    def check_url(_url, _method, _endpoint, _response):
        urls = url_map.bind_to_environ(MockEnv(_url, _method))
        endpoint, kwargs = urls.match()
        assert endpoint == _endpoint, u"Should have chosen the correct function"
        res = _locals[endpoint]("p1", **kwargs)
        print res, _response
        assert res == _response

    check_url(u"/test", u"GET", u"get", u"GET p1")
    check_url(u"/test", u"POST", u"post", u"POST p1")
    check_url(u"/test_both", u"GET", u"post_and_get", u"GET POST p1")
    check_url(u"/test_both", u"POST", u"post_and_get", u"GET POST p1")

