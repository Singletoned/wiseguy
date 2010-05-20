# -*- coding: utf-8 -*-

import collections
import functools
from StringIO import StringIO

from nose.tools import assert_equal, assert_raises

import werkzeug
from werkzeug import Request, Response, redirect, html

from lxml.html import tostring

import wiseguy
from wiseguy.webtest import TestAgent

tostring = functools.partial(tostring, encoding="utf-8")

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
        return Response([
                '; '.join(
                    "%s:<%s>" % (name, value)
                    for (name, value) in items
                )
        ])(environ, start_response)


url_map = werkzeug.routing.Map()

def match(rule, method):
    def decorate(f):
        r = werkzeug.routing.Rule(rule, methods=[method], endpoint=f)
        url_map.add(r)
        return f
    return decorate

class TestApp(object):
    def __call__(self, environ, start_response):
        request = Request(environ)
        request.url_map = url_map.bind_to_environ(environ)
        try:
            endpoint, kwargs = request.url_map.match()
            response = endpoint(request, **kwargs)
        except werkzeug.exceptions.HTTPException, e:
            response = e
        return response(environ, start_response)

    @match('/redirect1', 'GET')
    def redirect1(request):
        return redirect('/redirect2')

    @match('/redirect2', 'GET')
    def redirect2(request):
        return redirect('/page1')

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

    @match('/page2', 'GET')
    @page('''<html><html>''')
    def page2(request):
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

    @match('/bad-link', 'GET')
    @page('''
        <html><body>
        <a href="page_that_does_not_exist">A Bad Link</a>
        </body></html>
    ''')
    def bad_link(request):
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
                '; '.join("%s:<%s>" % (name, value) for (name, value) in sorted(request.form.items(multi=True)))
        ])

    @match('/getform', 'GET')
    def form_submit(request):
        return Response([
                '; '.join("%s:<%s>" % (name, value) for (name, value) in sorted(request.args.items(multi=True)))
        ])

    @match('/setcookie', 'GET')
    def setcookie(request, name='', value='', path=''):
        name = name or request.args['name']
        value = value or request.args['value']
        path = path or request.args.get('path', None) or '/'
        response = Response(['ok'])
        response.set_cookie(name, value, path=path)
        return response

    @match('/cookies', 'GET')
    @match('/<path:path>/cookies', 'GET')
    def listcookies(request, path=None):
        return Response([
                '; '.join("%s:<%s>" % (name, value) for (name, value) in sorted(request.cookies.items()))
        ])

def test_one():
    page = TestAgent(TestApp()).get('/page1')
    assert_raises(
        wiseguy.webtest.MultipleMatchesError,
        page.one,
        "//a"
    )
    assert_raises(
        wiseguy.webtest.NoMatchesError,
        page.one,
        "//h1"
    )

def test_reset():
    agent = TestAgent(TestApp())
    assert_raises(
        wiseguy.webtest.NoRequestMadeError,
        agent.reset
    )
    page = agent.get(u'/form-text')
    assert page.one(u"//input[@name='a'][1]").value == u'a'
    page.one(u"//input[@name='a'][1]").value = u'foobar'
    assert page.one(u"//input[@name='a'][1]").value == u'foobar'
    page.reset()
    assert page.one(u"//input[@name='a'][1]").value == u'a'
    input_b = page.one(u"//input[@name='b']")
    assert input_b.value == u''
    input_b.value = u'flibble'
    assert input_b.value == u'flibble'
    page.reset()
    print input_b.value
    assert input_b.value == u''

def test_click():
    page = TestAgent(TestApp()).get('/page1')
    assert_equal(
        page.one("//a[1]").click().request.path,
        '/page1'
    )
    assert_equal(
        page.one("//a[2]").click().request.path,
        '/page2'
    )
    assert_equal(
        len(page.all("//a")),
        3
    )
    assert_raises(
        wiseguy.webtest.MultipleMatchesError,
        page.one,
        "//a"
    )

def test_rows_to_dict():
    body = """
<table>
  <tr>
    <th>foo</th> <th>bar</th> <th>baz</th>
  </tr>
  <tr>
    <td>1</td> <td>2</td> <td>3</td>
  </tr>
  <tr>
    <td>4</td> <td>5</td> <td>6</td>
  </tr>
</table>
    """
    agent = TestAgent(Response(body)).get('/')
    row = agent.one(u'//tr[td][1]')
    expected = dict(foo='1', bar='2', baz='3')
    for key in expected:
        assert_equal(expected[key], row.to_dict()[key])

def test_tables():
    header_values = ["foo", "bar", "baz"]
    table_text = html.table(
        html.tr(
            *[html.th(i) for i in header_values]),
        html.tr(
            *[html.td(i) for i in [1, 2, 3]]),
        html.tr(
            *[html.td(i) for i in [4, 5, 6]]))
    agent = TestAgent(Response([table_text])).get(u'/')
    table = agent.one(u"//table")
    rows = [row.to_dict() for row in table.rows()]
    headers = table.headers()
    assert len(headers) == 3
    assert headers == header_values
    assert len(rows) == 2
    for i, row in enumerate(rows):
        for j, header in enumerate(header_values):
            index = (i * 3) + (j + 1)
            assert row[header] == str(index)
            assert row[header] == type(row[header])(index)
        for j, cell in enumerate(row.values()):
            index = (i * 3) + (j + 1)
            assert cell == str(index)
    TestObject = collections.namedtuple('TestObject', header_values)
    obj_1 = TestObject(1, 2, 3)
    obj_2 = TestObject(4, 5, 6)
    for row, obj in zip(table.rows(), [obj_1, obj_2]):
        row.assert_has_object(obj)

def test_unicode_chars():
    body_text = html.div(
        html.p(u"£")).encode('utf-8')
    agent = TestAgent(Response([body_text]))
    page = agent.get(u'/')
    assert page.body == body_text
    assert tostring(page.lxml) == body_text
    assert page.html() == body_text
    div_element = page.one('//div')
    assert div_element.html() == body_text
    assert tostring(div_element.lxml) == body_text

def test_lxml_attr_is_consistent():
    body_text = html.div(
        html.p(u"foo")).encode('utf-8')
    agent = TestAgent(Response([body_text]))
    page = agent.get(u'/')
    div_element = page.one('//div')
    assert page.lxml == div_element.lxml

def test_lxml_attr_doesnt_reset_forms():
    form_page = TestAgent(TestApp()).get('/form-text')
    form = form_page.one('//form')
    # Set field values
    form.one('//input[@name="a"][1]').value = 'do'
    form.one('//input[@name="a"][2]').value = 're'
    form.one('//input[@name="b"][1]').value = 'mi'
    # Check page body
    assert "form" in tostring(form_page.lxml)
    # Check form values
    assert form.one('//input[@name="a"][1]').value == 'do'
    assert form.one('//input[@name="a"][2]').value == 're'
    assert form.one('//input[@name="b"][1]').value == 'mi'

def test_css_selectors_are_equivalent_to_xpath():
    page = TestAgent(TestApp()).get('/page1')
    assert_equal(
        list(page.all('//a')),
        list(page.all('a', css=True))
    )

def test_get_with_query_is_correctly_handled():
    page = TestAgent(TestApp()).get('/getform?x=1')
    assert_equal(page.body, "x:<1>")

def test_click_follows_redirect():
    page = TestAgent(TestApp()).get('/page1')
    link = page.one("//a[text()='redirect']")
    response = link.click(follow=False)
    assert_equal(response.request.path, '/redirect1')

    page = TestAgent(TestApp()).get('/page1')
    link = page.one("//a[text()='redirect']")
    response = link.click(follow=True)
    assert_equal(response.request.path, '/page1')

def test_click_404_raises_error():
    page = TestAgent(TestApp()).get('/bad-link')
    link = page.one("//a[text()='A Bad Link']")
    assert_raises(
        wiseguy.webtest.PageNotFound,
        link.click
    )

def test_form_text():
    form_page = TestAgent(TestApp()).get('/form-text')
    form = form_page.one('//form')
    # Check defaults are submitted
    assert_equal(
        form.submit().body,
        "a:<>; a:<a>; b:<>"
    )

    # Now set field values
    form.one('//input[@name="a"][1]').value = 'do'
    form.one('//input[@name="a"][2]').value = 're'
    form.one('//input[@name="b"][1]').value = 'mi'
    assert_equal(
        form.submit().body,
        "a:<do>; a:<re>; b:<mi>"
    )

def test_form_checkbox():
    form_page = TestAgent(TestApp()).get('/form-checkbox')
    form = form_page.one('//form')
    # Check defaults are submitted
    assert_equal(
        form.submit().body,
        "b:<A>"
    )

    # Now set field values
    form.one('//input[@name="a"][1]').checked = True
    form.one('//input[@name="a"][2]').checked = True
    form.one('//input[@name="b"][1]').checked = False
    form.one('//input[@name="b"][2]').checked = True
    assert_equal(
        form.submit().body,
        "a:<1>; a:<2>; b:<B>"
    )

def test_form_getitem():
    form_text = html.div(
        html.p(
            html.input(type="text", name="foo", value="flam")),
        html.p(
            html.select(
                html.option(value="a", selected=True),
                html.option(value="b"),
                name="bar"))
    )
    form_page = TestAgent(FormApp(form_text)).get(u'/')
    form = form_page.one(u'//form')
    assert form['foo'] == "flam"
    assert form['bar'] == "a"
    form["foo"] = u"flibble"
    form["bar"] = u"a"
    assert form.one(u'//input').value == u'flibble'
    assert form.one(u'//select').value == u'a'

def test_form_getitem_doesnt_match():
    form_text = html.body(
        html.form(
            html.input(name="foo", value="a")),
        html.input(name="foo", value="b"))
    agent = TestAgent(Response([form_text]))
    form_page = agent.get(u'/')
    form = form_page.one(u"//form")
    assert form[u"foo"] == u"a"

def test_form_textarea():
    form_page = TestAgent(FormApp('<textarea name="t"></textarea>')).get('/')
    el = form_page.one('//textarea')
    el.value = 'test'
    assert_equal(
        form_page.one('//textarea').form.submit().body,
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
    r.one('//select').value = 'o2'
    assert_equal(r.one('//form').submit().body, 's:<o2>')

    r = TestAgent(app).get('/')
    r.one('//select/option[2]').selected = True
    r.one('//select/option[1]').selected = True
    assert_equal(r.one('//form').submit().body, 's:<o1>')

def test_form_select_multiple():
    app = FormApp("""
        <select name="s" multiple="">
        <option value="o1"></option>
        <option value="o2"></option>
        <option value="o3"></option>
        </select>
    """)
    r = TestAgent(app).get('/')
    r.one('//select').value = ['o1', 'o3']
    assert_equal(r.one('//form').submit().body, 's:<o1>; s:<o3>')

    r = TestAgent(app).get('/')
    r.one('//select/option[3]').selected = True
    r.one('//select/option[2]').selected = True
    assert_equal(r.one('//form').submit().body, 's:<o2>; s:<o3>')

def test_form_radio():
    app = FormApp("""
        <input name="a" value="1" type="radio"/>
        <input name="a" value="2" type="radio"/>
        <input name="b" value="3" type="radio"/>
        <input name="b" value="4" type="radio"/>
    """)
    r = TestAgent(app).get('/')
    r.all('//*[@name="a"]')[0].checked = True
    r.all('//*[@name="b"]')[0].checked = True
    assert_equal(r.one('//form').submit().body, 'a:<1>; b:<3>')

    r = TestAgent(app).get('/')
    r.one('//*[@name="a"][1]').checked = True
    r.one('//*[@name="a"][2]').checked = True
    assert_equal(r.one('//form').submit().body, 'a:<2>')

def test_form_hidden():
    form_page = TestAgent(FormApp('<input name="t" value="1" type="hidden"/>')).get('/')
    assert_equal(
        form_page.one('//form').form.submit().body,
        't:<1>'
    )


def test_form_disabled():
    form_page = TestAgent(FormApp('<input name="t" value="1" type="text" disabled="" />')).get('/')
    assert_equal(
        form_page.one('//form').form.submit().body,
        ''
    )


def test_form_input_no_type():
    form_page = TestAgent(FormApp('<input name="t" value="1" />')).get('/')
    assert_equal(form_page.one('//form').form.submit().body, 't:<1>')

def test_form_file_input_value_requires_3tuple():
    r = TestAgent(FormApp('<input name="upload" type="file" />')).get('/')
    try:
        r.one('//input').value = 'photo.jpg'
    except ValueError:
        pass
    else:
        raise AssertionError("Expecting a ValueError")

    r = TestAgent(FormApp('<input name="upload" type="file" />')).get('/')
    try:
        r.one('//input').value = ('photo.jpg', '123123')
    except ValueError:
        pass
    else:
        raise AssertionError("Expecting a ValueError")

    r.one('//input').value = ('photo.jpg', 'text/jpeg', '123123')

def test_form_file_input_requires_stores_values():
    r = TestAgent(FormApp('<input name="upload" type="file" />')).get('/')
    r.one('//input').value = ('photo.jpg', 'text/jpeg', '123123')
    assert_equal(r.one('//input').value, ('photo.jpg', 'text/jpeg', '123123'))

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
    r.one('//input').value = ('photo.jpg', 'text/jpeg', '123123')
    r.one('//form').submit()

    r = TestAgent(TestApp('<input name="upload" type="file" />', enctype="multipart/form-data")).get('/')
    r.one('//input').value = ('photo.jpg', 'text/jpeg', StringIO('123123'))
    r.one('//form').submit()


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

    assert_equal(form_page.one('//form').submit().body, '')
    assert_equal(form_page.one('//form').submit_data(), [])

    assert_equal(form_page.one('#1', css=True).submit().body, 's:<1>')
    assert_equal(form_page.one('#1', css=True).submit_data(), [('s', '1')])
    assert_equal(form_page.one('#2', css=True).submit().body, 's:<2>')
    assert_equal(form_page.one('#2', css=True).submit_data(), [('s', '2')])
    assert_equal(form_page.one('#3', css=True).submit().body, 't:<3>')
    assert_equal(form_page.one('#3', css=True).submit_data(), [('t', '3')])
    assert_equal(form_page.one('#4', css=True).submit().body, 'u:<4>; u.x:<1>; u.y:<1>')
    assert_equal(form_page.one('#4', css=True).submit_data(), [('u', '4'), ('u.x', '1'), ('u.y', '1')])
    assert_equal(form_page.one('#5', css=True).submit().body, 'v:<5>')
    assert_equal(form_page.one('#5', css=True).submit_data(), [('v', '5')])
    assert_equal(form_page.one('#6', css=True).submit().body, 'w:<6>')
    assert_equal(form_page.one('#6', css=True).submit_data(), [('w', '6')])
    try:
        form_page.one('#7', css=True).submit()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Shouldn't be able to submit a non-submit button")

    try:
        form_page.one('#7', css=True).submit_data()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Shouldn't be able to call submit_data on a non-submit button")

def test_form_action_fully_qualified_uri_doesnt_error():
    app = FormApp("", action='http://localhost/')
    r = TestAgent(app).get('/')
    assert_equal(r.one('//form').submit().body, '')

def test_form_submit_follows_redirect():
    form_page = TestAgent(TestApp()).get('/form-text')
    form_page.one('//form').attrib['method'] = 'get'
    form_page.one('//form').attrib['action'] = '/redirect1'
    assert_equal(
        form_page.one('//form').submit(follow=True).request.path,
        '/page1'
    )

def test_form_attribute_returns_parent_form():
    form_page = TestAgent(TestApp()).get('/form-text')
    assert_equal(form_page.all('//input[@name="a"]')[0].form, form_page.one('//form'))

def test_cookies_are_received():
    response = TestAgent(TestApp()).get('/setcookie?name=foo&value=bar&path=/')
    assert_equal(response.cookies['foo'].value, 'bar')
    assert_equal(response.cookies['foo']['path'], '/')

def test_cookies_are_resent():
    response = TestAgent(TestApp()).get('/setcookie?name=foo&value=bar&path=/')
    response = response.get('/cookies')
    assert_equal(response.body, 'foo:<bar>')

def test_cookie_paths_are_observed():
    response = TestAgent(TestApp()).get('/setcookie?name=doobedo&value=dowop&path=/')
    response = response.get('/setcookie?name=dowahdowah&value=beebeebo&path=/private')

    response = response.get('/cookies')
    assert_equal(response.body, 'doobedo:<dowop>')

    response = response.get('/private/cookies')
    assert_equal(response.body, 'doobedo:<dowop>; dowahdowah:<beebeebo>')

def test_back_method_returns_agent_to_previous_state():
    saved = agent = TestAgent(TestApp()).get('/page1')
    agent = agent.one("//a[.='page 2']").click()
    assert agent.request.path == '/page2'
    agent = agent.back()
    assert agent.request.path == '/page1'
    assert agent is saved

def test_back_method_skips_redirects():
    saved = agent = TestAgent(TestApp()).get('/page2')
    agent = agent.get('/redirect1', follow=True)
    assert agent.request.path == '/page1'
    agent = agent.back()
    assert agent.request.path == '/page2'
    assert agent is saved

def test_context_manager_allows_checkpointing_history():
    saved = agent = TestAgent(TestApp()).get('/page1')

    with agent as a2:
        a2 = a2.one("//a[.='page 2']").click()
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
    assert 'tea tray' in agent.one('//p')
    assert 'tea tray' in agent.all('//p')[0]
    assert 'teat ray' not in agent.one('//p')
    assert 'teat ray' not in agent.all('//p')[0]

def test_regexes_enabled_in_xpath():
    agent = TestAgent(Response(['<html><p>salt</p><p>pepper</p><p>pickle</p>'])).get('/')
    assert [tag.text for tag in agent._find("//*[re:test(text(), '^p')]")] == ['pepper', 'pickle']
    assert [tag.text for tag in agent._find("//*[re:test(text(), '.*l')]")] == ['salt', 'pickle']

# def test_get_allows_relative_uri():
#     agent = TestAgent(Response(['<html><p>salt</p><p>pepper</p><p>pickle</p>']))
#     try:
#         agent.get('../')
#     except AssertionError:
#         # Expect an AssertionError, as we haven't made an initial request to be
#         # relative to
#         pass
#     else:
#         raise AssertionError("Didn't expect relative GET request to work")
#     agent = agent.get('/rhubarb/custard/')
#     agent = agent.get('../')
#     assert_equal(agent.request.url, 'http://localhost/rhubarb')

