# -*- coding: utf-8 -*-

import wiseguy.web_utils
import werkzeug as wz
import jinja2

url_map = wiseguy.web_utils.UrlMap()

@url_map.expose(u"/")
@wiseguy.web_utils.render('index.html')
def index(request):
    return wiseguy.web_utils.JinjaResponse(
        "index.html",
        dict(greeting="Hello", name="World"))

renderer = wiseguy.web_utils.JinjaRenderer(
    jinja2.Environment(
        loader=jinja2.DictLoader(
            {'index.html': "<html><body><p>{{greeting}}, {{name}}!</p></body></html>"})))

application = wiseguy.web_utils.BaseApp(
    config=dict(),
    url_map=url_map,
    renderer=renderer)
application = wiseguy.web_utils.wsgi_wrapper(application)

def test_hello_world():
    import testino
    agent = testino.TestAgent(application)
    page = agent.get("/")
    assert page.one("//p[text()=$text]", text="Hello, World!")
