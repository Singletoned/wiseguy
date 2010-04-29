from StringIO import StringIO

from nose.tools import assert_equal

from werkzeug import Request

from wiseguy.webtest import TestAgent

from pesto import dispatcher_app, Response
# from pesto.request import Request
from pesto.wsgiutils import with_request_args
dispatcher = dispatcher_app()
match = dispatcher.match

def page(html):
    def page(func):
        def page(request, *args, **kwargs):
            return Response(html % (func(request, *args, **kwargs)))
        return page
    return page

class FormApp(object):
    """
    A WSGI application that responds to GET requests with the given
    HTML, and POST requests with a dump of the posted info
    """


    def __init__(self, formhtml, action=None, enctype="application/x-www-form-urlencoded"):

        if action is None:
            action = "/"

        self.formhtml = formhtml
        self.action = action
        self.enctype = enctype

    def __call__(self, environ, start_response):
        return getattr(self, environ['REQUEST_METHOD'])(environ, start_response)

    def GET(self, environ, start_response):
        return Response(
            [
                '<html><body><form method="POST" action="%s" enctype="%s">%s</form></body></html>' % (
                    self.action,
                    self.enctype,
                    self.formhtml,
                )
            ]
        )(environ, start_response)

    def POST(self, environ, start_response):
        items = sorted(Request(environ).form.items(multi=True))
        print items
        return Response([
                '; '.join(
                    "%s:<%s>" % (name, value)
                    for (name, value) in items
                )
        ])(environ, start_response)

class testapp(object):

    @match('/redirect1', 'GET')
    def redirect1(request):
        return Response.redirect('/redirect2')

    @match('/redirect2', 'GET')
    def redirect2(request):
        return Response.redirect('/page1')

    @match('/page1', 'GET')
    @page('''
          <html><body>
          <a href="page1">page 1</a>
          <a href="page2">page 2</a>
          <a href="redirect1">redirect</a>
          </body></html>
    ''')
    def page1(request):
        return {}

    @match('/form-text', 'GET')
    @page('''
          <html><body>
          <form method="POST" action="/postform">
            <input name="a" value="a" type="text" />
            <input name="a" value="" type="text" />
            <input name="b" value="" type="text" />
          </form>
          </body></html>
    ''')
    def form_text(request):
        return {}

    @match('/form-checkbox', 'GET')
    @page('''
          <html><body>
          <form method="POST" action="/postform">
            <input name="a" value="1" type="checkbox" />
            <input name="a" value="2" type="checkbox" />
            <input name="b" value="A" type="checkbox" checked="checked" />
            <input name="b" value="B" type="checkbox" />
          </form>
          </body></html>
    ''')
    def form_checkbox(request):
        return {}


    @match('/postform', 'POST')
    def form_submit(request):
        return Response([
                '; '.join("%s:<%s>" % (name, value) for (name, value) in sorted(request.form.allitems()))
        ])

    @match('/getform', 'GET')
    def form_submit(request):
        return Response([
                '; '.join("%s:<%s>" % (name, value) for (name, value) in sorted(request.query.allitems()))
        ])

    @match('/setcookie', 'GET')
    @with_request_args(name=unicode, value=unicode, path=unicode)
    def setcookie(request, name='foo', value='bar', path='/'):
        return Response(['ok']).add_cookie(name, value, path=path)

    @match('/cookies', 'GET')
    @match('/<path:path>/cookies', 'GET')
    def listcookies(request, path=None):
        return Response([
                '; '.join("%s:<%s>" % (name, value.value) for (name, value) in sorted(request.cookies.allitems()))
        ])

def test_click():
    page = TestAgent(dispatcher).get('/page1')
    assert_equal(
        page["//a[1]"].click().request.path,
        '/page1'
    )
    assert_equal(
        page["//a[2]"].click().request.path,
        '/page2'
    )

def test_css_selectors_are_equivalent_to_xpath():
    page = TestAgent(dispatcher).get('/page1')
    assert_equal(
        list(page.find('//a')),
        list(page.findcss('a'))
    )

def test_get_with_query_is_correctly_handled():
    page = TestAgent(dispatcher).get('/getform?x=1')
    assert_equal(page.body, "x:<1>")

def test_click_follows_redirect():

    response = TestAgent(dispatcher).get('/page1')["//a[text()='redirect']"].click(follow=False)
    assert_equal(response.request.path, '/redirect1')

    response = TestAgent(dispatcher).get('/page1')["//a[text()='redirect']"].click(follow=True)
    assert_equal(response.request.path, '/page1')

def test_form_text():
    form_page = TestAgent(dispatcher).get('/form-text')
    form = form_page['//form']
    # Check defaults are submitted
    assert_equal(
        form.submit().body,
        "a:<>; a:<a>; b:<>"
    )

    # Now set field values
    form['//input[@name="a"][1]'].value = 'do'
    form['//input[@name="a"][2]'].value = 're'
    form['//input[@name="b"][1]'].value = 'mi'
    assert_equal(
        form.submit().body,
        "a:<do>; a:<re>; b:<mi>"
    )

def test_form_checkbox():
    form_page = TestAgent(dispatcher).get('/form-checkbox')
    form = form_page['//form']
    # Check defaults are submitted
    assert_equal(
        form.submit().body,
        "b:<A>"
    )

    # Now set field values
    form['//input[@name="a"][1]'].checked = True
    form['//input[@name="a"][2]'].checked = True
    form['//input[@name="b"][1]'].checked = False
    form['//input[@name="b"][2]'].checked = True
    assert_equal(
        form.submit().body,
        "a:<1>; a:<2>; b:<B>"
    )

def test_form_textarea():
    form_page = TestAgent(FormApp('<textarea name="t"></textarea>')).get('/')
    el = form_page['//textarea']
    el.value = 'test'
    assert_equal(
        form_page['//textarea'].form.submit().body,
        't:<test>'
    )

def test_form_select():
    app = FormApp("""
        <select name="s">
        <option value="o1"></option>
        <option value="o2"></option>
        </select>
    """)
    r = TestAgent(app).get('/')
    r['//select'].value = 'o2'
    assert_equal(r['//form'].submit().body, 's:<o2>')

    r = TestAgent(app).get('/')
    r['//select/option[2]'].selected = True
    r['//select/option[1]'].selected = True
    assert_equal(r['//form'].submit().body, 's:<o1>')

def test_form_select_multiple():
    app = FormApp("""
        <select name="s" multiple="">
        <option value="o1"></option>
        <option value="o2"></option>
        <option value="o3"></option>
        </select>
    """)
    r = TestAgent(app).get('/')
    r['//select'].value = ['o1', 'o3']
    assert_equal(r['//form'].submit().body, 's:<o1>; s:<o3>')

    r = TestAgent(app).get('/')
    r['//select/option[3]'].selected = True
    r['//select/option[2]'].selected = True
    assert_equal(r['//form'].submit().body, 's:<o2>; s:<o3>')

def test_form_radio():
    app = FormApp("""
        <input name="a" value="1" type="radio"/>
        <input name="a" value="2" type="radio"/>
        <input name="b" value="3" type="radio"/>
        <input name="b" value="4" type="radio"/>
    """)
    r = TestAgent(app).get('/')
    r['//*[@name="a"]'].value = '1'
    r['//*[@name="b"]'].value = '3'
    assert_equal(r['//form'].submit().body, 'a:<1>; b:<3>')

    r = TestAgent(app).get('/')
    r['//*[@name="a"][1]'].checked = True
    r['//*[@name="a"][2]'].checked = True
    assert_equal(r['//form'].submit().body, 'a:<2>')

def test_form_hidden():
    form_page = TestAgent(FormApp('<input name="t" value="1" type="hidden"/>')).get('/')
    assert_equal(
        form_page['//form'].form.submit().body,
        't:<1>'
    )


def test_form_disabled():
    form_page = TestAgent(FormApp('<input name="t" value="1" type="text" disabled="" />')).get('/')
    assert_equal(
        form_page['//form'].form.submit().body,
        ''
    )


def test_form_input_no_type():
    form_page = TestAgent(FormApp('<input name="t" value="1" />')).get('/')
    assert_equal(form_page['//form'].form.submit().body, 't:<1>')

def test_form_file_input_value_requires_3tuple():
    r = TestAgent(FormApp('<input name="upload" type="file" />')).get('/')
    try:
        r['//input'].value = 'photo.jpg'
    except ValueError:
        pass
    else:
        raise AssertionError("Expecting a ValueError")

    r = TestAgent(FormApp('<input name="upload" type="file" />')).get('/')
    try:
        r['//input'].value = ('photo.jpg', '123123')
    except ValueError:
        pass
    else:
        raise AssertionError("Expecting a ValueError")

    r['//input'].value = ('photo.jpg', 'text/jpeg', '123123')

def test_form_file_input_requires_stores_values():
    r = TestAgent(FormApp('<input name="upload" type="file" />')).get('/')
    r['//input'].value = ('photo.jpg', 'text/jpeg', '123123')
    assert_equal(r['//input'].value, ('photo.jpg', 'text/jpeg', '123123'))

def test_form_file_input_submits_file_data():

    class TestApp(FormApp):
        def POST(self, environ, start_response):
            from werkzeug import FileStorage
            req = Request(environ)
            fu = req.files['upload']
            assert isinstance(fu, FileStorage)
            assert fu.read() == '123123'
            return Response(['ok'])(environ, start_response)

    r = TestAgent(TestApp('<input name="upload" type="file" />', enctype="multipart/form-data")).get('/')
    r['//input'].value = ('photo.jpg', 'text/jpeg', '123123')
    r['//form'].submit()

    r = TestAgent(TestApp('<input name="upload" type="file" />', enctype="multipart/form-data")).get('/')
    r['//input'].value = ('photo.jpg', 'text/jpeg', StringIO('123123'))
    r['//form'].submit()


def test_form_submit_button():
    app = FormApp('''
        <input id="1" type="submit" name="s" value="1"/>
        <input id="2" type="submit" name="s" value="2"/>
        <input id="3" type="submit" name="t" value="3"/>
        <input id="4" type="image" name="u" value="4"/>
        <button id="5" type="submit" name="v" value="5">click me!</button>
        <button id="6" name="w" value="6">click me!</button>
        <button id="7" type="button" name="x" value="7">don't click me!</button>
    ''')
    form_page = TestAgent(app).get('/')

    assert_equal(form_page['//form'].submit().body, '')
    assert_equal(form_page['//form'].submit_data(), [])

    assert_equal(form_page.findcss('#1').submit().body, 's:<1>')
    assert_equal(form_page.findcss('#1').submit_data(), [('s', '1')])
    assert_equal(form_page.findcss('#2').submit().body, 's:<2>')
    assert_equal(form_page.findcss('#2').submit_data(), [('s', '2')])
    assert_equal(form_page.findcss('#3').submit().body, 't:<3>')
    assert_equal(form_page.findcss('#3').submit_data(), [('t', '3')])
    assert_equal(form_page.findcss('#4').submit().body, 'u:<4>; u.x:<1>; u.y:<1>')
    assert_equal(form_page.findcss('#4').submit_data(), [('u', '4'), ('u.x', '1'), ('u.y', '1')])
    assert_equal(form_page.findcss('#5').submit().body, 'v:<5>')
    assert_equal(form_page.findcss('#5').submit_data(), [('v', '5')])
    assert_equal(form_page.findcss('#6').submit().body, 'w:<6>')
    assert_equal(form_page.findcss('#6').submit_data(), [('w', '6')])
    try:
        form_page.findcss('#7').submit()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Shouldn't be able to submit a non-submit button")

    try:
        form_page.findcss('#7').submit_data()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Shouldn't be able to call submit_data on a non-submit button")

def test_form_action_fully_qualified_uri_doesnt_error():
    app = FormApp("", action='http://localhost/')
    r = TestAgent(app).get('/')
    assert_equal(r['//form'].submit().body, '')

def test_form_submit_follows_redirect():
    form_page = TestAgent(dispatcher).get('/form-text')
    form_page['//form'].attrib['method'] = 'get'
    form_page['//form'].attrib['action'] = '/redirect1'
    assert_equal(
        form_page['//form'].submit(follow=True).request.path,
        '/page1'
    )

def test_form_attribute_returns_parent_form():
    form_page = TestAgent(dispatcher).get('/form-text')
    assert_equal(form_page['//input[@name="a"]'].form, form_page['//form'][0])

def test_cookies_are_received():
    response = TestAgent(dispatcher).get('/setcookie?name=foo;value=bar;path=/')
    assert_equal(response.cookies['foo'].value, 'bar')
    assert_equal(response.cookies['foo']['path'], '/')

def test_cookies_are_resent():
    response = TestAgent(dispatcher).get('/setcookie?name=foo;value=bar;path=/')
    response = response.get('/cookies')
    assert_equal(response.body, 'foo:<bar>')

def test_cookie_paths_are_observed():
    response = TestAgent(dispatcher).get('/setcookie?name=doobedo;value=dowop;path=/')
    response = response.get('/setcookie?name=dowahdowah;value=beebeebo;path=/private')

    response = response.get('/cookies')
    assert_equal(response.body, 'doobedo:<dowop>')

    response = response.get('/private/cookies')
    assert_equal(response.body, 'doobedo:<dowop>; dowahdowah:<beebeebo>')

def test_back_method_returns_agent_to_previous_state():
    saved = agent = TestAgent(dispatcher).get('/page1')
    agent = agent["//a[.='page 2']"].click()
    assert agent.request.path == '/page2'
    agent = agent.back()
    assert agent.request.path == '/page1'
    assert agent is saved

def test_back_method_skips_redirects():
    saved = agent = TestAgent(dispatcher).get('/page2')
    agent = agent.get('/redirect1', follow=True)
    assert agent.request.path == '/page1'
    agent = agent.back()
    assert agent.request.path == '/page2'
    assert agent is saved

def test_context_manager_allows_checkpointing_history():
    saved = agent = TestAgent(dispatcher).get('/page1')

    with agent as a2:
        a2 = a2["//a[.='page 2']"].click()
        assert a2.request.path == '/page2'

    assert agent.request.path == '/page1'
    assert agent is saved

def test_html_method_returns_string_representation():
    agent = TestAgent(Response(['<p>I would like an ice lolly</p>'])).get('/')
    assert_equal(
        agent.root_element.html(),
        '<p>I would like an ice lolly</p>'
    )

def test_striptags_method_returns_string_representation():
    agent = TestAgent(Response(['<p>And a nice <strong>cup of tea</strong>!</p>'])).get('/')
    assert_equal(
        agent.root_element.striptags(),
        'And a nice cup of tea!'
    )

def test_in_operator_works_on_elementwrapper():
    agent = TestAgent(Response(['<p>Tea tray tea tray tea tray tea tray</p>'])).get('/')
    assert 'tea tray' in agent['//p']
    assert 'tea tray' in agent['//p'][0]

def test_regexes_enabled_in_xpath():
    agent = TestAgent(Response(['<html><p>salt</p><p>pepper</p><p>pickle</p>'])).get('/')
    assert [tag.text for tag in agent.find("//*[re:test(text(), '^p')]")] == ['pepper', 'pickle']
    assert [tag.text for tag in agent.find("//*[re:test(text(), '.*l')]")] == ['salt', 'pickle']

def test_get_allows_relative_uri():

    agent = TestAgent(Response(['<html><p>salt</p><p>pepper</p><p>pickle</p>']))
    try:
        agent.get('../')
    except AssertionError:
        # Expect an AssertionError, as we haven't made an initial request to be
        # relative to
        pass
    else:
        raise AssertionError("Didn't expect relative GET request to work")
    agent = agent.get('/rhubarb/custard/')
    agent = agent.get('../')
    assert_equal(agent.request.url, 'http://localhost/rhubarb')

