# -*- coding: utf-8 -*-

import wiseguy.web_utils
import werkzeug as wz
import jinja2

url_map = wiseguy.web_utils.UrlMap()

@url_map.expose(u"/")
@wiseguy.web_utils.render('index.html')
def index(request):
    return dict(greeting="Hello", name="World")

env = wiseguy.web_utils.JinjaEnv(
    jinja2.Environment(
        loader=jinja2.DictLoader(
            {'index.html': "<p>{{greeting}}, {{name}}!</p>"})))

application = wiseguy.web_utils.BaseApp(
    config=dict(),
    url_map=url_map,
    env=env)

def test_hello_world():
    import testino
    agent = testino.TestAgent(application)
    page = agent.get("/")
    assert page.one("//p[text()=$text]", text="Hello, World!")
