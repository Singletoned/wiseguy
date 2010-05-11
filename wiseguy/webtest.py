from wsgiref.validate import validator as wsgi_validator
from cStringIO import StringIO
from urlparse import urlparse, urlunparse, urljoin
from Cookie import BaseCookie
from functools import wraps
from itertools import chain
from shutil import copyfileobj
import re

import lxml.html
from lxml.cssselect import CSSSelector
from lxml.etree import XPath

import werkzeug
from werkzeug import Request, Response

# Registry for xpath multimethods
xpath_registry = {}

# EXSLT regular expression namespace URI
REGEXP_NAMESPACE = "http://exslt.org/regular-expressions"

class MultipleMatchesError(Exception):
    def __init__(self, path, elements):
        self.path = path
        self.elements = elements

    def __str__(self):
        return "%s returns multiple elements, %s" % (self.path, self.elements)

class NoMatchesError(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "%s returns no elements" % (self.path,)

class NoRequestMadeError(Exception):
    pass

class XPathMultiMethod(object):
    """
    A callable object that has different implementations selected by XPath
    expressions.
    """

    def __init__(self):
        self.__doc__ = ''
        self.endpoints = []

    def __call__(self, *args, **kwargs):
        el = args[0]
        el = getattr(el, 'element', el)
        for xpath, func in self.endpoints:
            if el in xpath(el):
                return func(*args, **kwargs)
        raise NotImplementedError("Function not implemented for element %r" % (el,))

    def register(self, xpath, func):
        self.endpoints.append((
            XPath(
                '|'.join('../%s' % item for item in xpath.split('|'))
            ),
            func
        ))
        if not func.func_doc:
            return

        # Add wrapped function to the object's docstring
        # Note that ".. comment block" is required to fool rst/sphinx into
        # correctly parsing the indented paragraphs when there is only one
        # registered endpoint.
        self.__doc__ += 'For elements matching ``%s``:\n%s\n\n.. comment block\n\n' % (
            xpath,
            '\n'.join('    %s' % line for line in func.func_doc.split('\n'))
        )

def when(xpath_expr):
    """
    Decorator for methods having different implementations selected by XPath
    expressions.
    """
    def when(func):
        if getattr(func, '__wrapped__', None):
            func = getattr(func, '__wrapped__')
        multimethod = xpath_registry.setdefault(func.__name__, XPathMultiMethod())
        multimethod.register(xpath_expr, func)
        wrapped = wraps(func)(
            lambda self, *args, **kwargs: multimethod(self, *args, **kwargs)
        )
        wrapped.__wrapped__ = func
        wrapped.func_doc = multimethod.__doc__
        return wrapped
    return when

class ElementWrapper(object):
    """
    Wrapper for an ``lxml.etree`` element, providing additional methods useful
    for driving/testing WSGI applications. ``ElementWrapper`` objects are
    normally created through the ``one``/``all`` methods of ``TestAgent``
    instance::

        >>> from werkzeug import Response
        >>> myapp = Response(['<html><body><a href="/">link 1</a><a href="/">link 2</a></body></html>'])
        >>> agent = TestAgent(myapp).get('/')
        >>> elementwrappers = agent.all('//a')

    ``ElementWrapper`` objects have many methods and properties implemented as
    ``XPathMultiMethod`` objects, meaning their behaviour varies depending on
    the type of element being wrapped. For example, form elements have a
    ``submit`` method, ``a`` elements have a ``click`` method, and ``input``
    elements have a value property.
    """

    def __init__(self, agent, element):
        self.agent = agent
        self.agent._elements.append(self)
        self.element = element
        self._lxml = lxml.html.tostring(self.element)

    def __str__(self):
        return str(self.element)

    def __repr__(self):
        return '<ElementWrapper %r>' % (self.element,)

    def __getattr__(self, attr):
        return getattr(self.element, attr)

    def one(self, xpath):
        """
        Return only one wrapped sub-element.  Raise
        MultipleMatchesError if more than one result
        """
        elements = self.element.xpath(xpath)
        if len(elements) == 0:
            raise NoMatchesError(xpath)
        elif len(elements) > 1:
            raise MultipleMatchesError(xpath, elements)
        else:
            return self.__class__(self.agent, elements[0])

    def all(self, xpath):
        """
        Return all matching wrapped sub-elements.
        """
        elements = self.element.xpath(xpath)
        return [self.__class__(self.agent, el) for el in elements]

    def reset(self):
        self.element = lxml.html.fromstring(self._lxml)

    @when("a[@href]")
    def click(self, follow=False):
        """
        Follow a link and return a new instance of ``TestAgent``
        """
        return self.agent._click(self, follow=follow)

    @when("input[@type='checkbox']")
    def _get_value(self):
        """
        Return the value of the selected checkbox attribute (defaults to ``On``)
        """
        return self.element.attrib.get('value', 'On')

    @when("input[@type='file']")
    def _set_value(self, value):
        """
        Set the value of the file upload, which must be a tuple of::

            (filename, content-type, data)

        Where data can either be a byte string or file-like object.
        """
        filename, content_type, data = value
        self.agent.file_uploads[self.element] = (filename, content_type, data)

        # Set the value in the DOM to the filename so that it can be seen when
        # the DOM is displayed
        self.element.attrib['value'] = filename

    @when("input[@type='file']")
    def _get_value(self):
        """
        Return the value of the file upload, which will be a tuple of
        ``(filename, content-type, data)``
        """
        return self.agent.file_uploads.get(self.element)

    @when("input|button")
    def _get_value(self):
        """
        Return the value of the input or button element
        """
        return self.element.attrib.get('value', '')

    @when("input|button")
    def _set_value(self, value):
        """
        Set the value of the input or button element
        """
        self.element.attrib['value'] = value

    @when("textarea")
    def _get_value(self):
        """
        Return the value of the textarea
        """
        return self.element.text

    @when("textarea")
    def _set_value(self, value):
        """
        Set the value of the textarea
        """
        self.element.text = value

    @when("select[@multiple]")
    def _get_value(self):
        """
        Return the value of the multiple select
        """
        return [item.attrib.get('value') for item in self.element.xpath('./option[@selected]')]

    @when("select[@multiple]")
    def _set_value(self, values):
        """
        Set the value of the multiple select to the given list of values
        """
        found = set()
        values = set(values)
        for el in self.element.xpath(".//option"):
            if (el.attrib['value'] in values):
                el.attrib['selected'] = ""
                found.add(el.attrib['value'])
            elif 'selected' in el.attrib:
                del el.attrib['selected']
        if found != values:
            raise AssertionError("Values %r not present in select %r" % (values - found, self.element.attrib.get('name')))

    @when("select")
    def _get_value(self):
        """
        Return the value of the (non-multiple) select box
        """
        try:
            return self.element.xpath('./option[@selected]')[0].attrib['value']
        except (KeyError, IndexError):
            return None

    @when("select")
    def _set_value(self, value):
        """
        Set the value of the (non-multiple) select to the given single value
        """
        found = False
        for el in self.element.xpath(".//option"):
            if (el.attrib.get('value') == value):
                el.attrib['selected'] = ""
                found = True
            elif 'selected' in el.attrib:
                del el.attrib['selected']
        if not found:
            raise AssertionError("Value %r not present in select %r" % (value, self.element.attrib.get('name')))


    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False
        return (
            self.element is other.element
            and self.agent is other.agent
        )

    value = property(_get_value, _set_value)

    @when("input[@type='radio' or @type='checkbox']")
    def submit_value(self):
        """
        Return the value of the selected radio/checkbox element as the user
        agent would return it to the server in a form submission.
        """
        if 'disabled' in self.element.attrib:
            return None
        if 'checked' in self.element.attrib:
            return self.value
        return None

    @when("input[not(@type) or @type != 'submit' and @type != 'image' and @type != 'reset']|select|textarea")
    def submit_value(self):
        """
        Return the value of any other input element as the user
        agent would return it to the server in a form submission.
        """

        if 'disabled' in self.element.attrib:
            return None
        return self.value

    @when("input[@type != 'submit' or @type != 'image' or @type != 'reset']")
    def submit_value(self):
        """
        Return the value of any submit/reset input element
        """
        return None

    submit_value = property(submit_value)

    def _get_checked(self, value):
        """
        Return True if the element has the checked attribute
        """
        return 'checked' in self.element.attrib

    @when("input[@type='radio']")
    def _set_checked(self, value):
        """
        Set the radio button state to checked (unchecking any others in the group)
        """
        for el in self.element.xpath(
            "./ancestor-or-self::form[1]//input[@type='radio' and @name=$name]",
            name=self.element.attrib.get('name', '')
        ):
            if 'checked' in el.attrib:
                del el.attrib['checked']

        if bool(value):
            self.element.attrib['checked'] = 'checked'
        else:
            if 'checked' in self.element.attrib:
                del self.element.attrib['checked']

    @when("input")
    def _set_checked(self, value):
        """
        Set the (checkbox) input state to checked
        """
        if bool(value):
            self.element.attrib['checked'] = 'checked'
        else:
            try:
                del self.element.attrib['checked']
            except KeyError:
                pass
    checked = property(_get_checked, _set_checked)

    @when("option")
    def _get_selected(self, value):
        """
        Return True if the given select option is selected
        """
        return 'selected' in self.element.attrib

    @when("option")
    def _set_selected(self, value):
        """
        Set the ``selected`` attribute for the select option element. If the
        select does not have the ``multiple`` attribute, unselect any
        previously selected option.
        """
        if 'multiple' not in self.element.xpath('./ancestor-or-self::select[1]')[0].attrib:
            for el in self.element.xpath("./ancestor-or-self::select[1]//option"):
                if 'selected' in el.attrib:
                    del el.attrib['selected']

        if bool(value):
            self.element.attrib['selected'] = ''
        else:
            if 'selected' in self.element.attrib:
                del self.element.attrib['selected']

    selected = property(_get_selected, _set_selected)

    @property
    @when("input|textarea|button|select|form")
    def form(self):
        """
        Return the form associated with the wrapped element.
        """
        return self.__class__(self.agent, self.element.xpath("./ancestor-or-self::form[1]")[0])

    @when("input[@type='submit' or @type='image']|button[@type='submit' or not(@type)]")
    def submit(self, follow=False):
        """
        Submit the form, returning a new ``TestAgent`` object, by clicking on
        the selected submit element (input of
        type submit or image, or button with type submit)
        """
        return self.form.submit(self, follow)

    @when("input[@type='submit' or @type='image']|button[@type='submit' or not(@type)]")
    def submit_data(self):
        """
        Submit the form, returning a new ``TestAgent`` object, by clicking on
        the selected submit element (input of
        type submit or image, or button with type submit)
        """
        return self.form.submit_data(self)

    @when("form")
    def submit(self, button=None, follow=False):
        """
        Submit the form, returning a new ``TestAgent`` object
        """
        method = self.element.attrib.get('method', 'GET').upper()
        data = self.submit_data(button)
        path = uri_join_same_server(
            self.agent.request.url,
            self.element.attrib.get('action', self.agent.request.path)
        )
        return {
            ('GET', None): self.agent.get,
            ('POST', None): self.agent.post,
            ('POST', 'application/x-www-form-urlencoded'): self.agent.post,
            ('POST', 'multipart/form-data'): self.agent.post_multipart,
        }[(method, self.element.attrib.get('enctype'))](path, data, follow=follow)

    @when("form")
    def submit_data(self, button=None):
        """
        Return a list of the data that would be submitted to the server
        in the format ``[(key, value), ...]``, without actually submitting the form.
        """
        data = []

        if button and 'name' in button.attrib:
            data.append((button.attrib['name'], button.value))
            if button.element.attrib.get('type') == 'image':
                data.append((button.attrib['name'] + '.x', '1'))
                data.append((button.attrib['name'] + '.y', '1'))

        for input in (ElementWrapper(self.agent, el) for el in self.element.xpath('.//input|.//textarea|.//select')):
            try:
                name = input.attrib['name']
            except KeyError:
                continue
            value = input.submit_value
            if value is None:
                continue

            elif input.attrib.get('type') == 'file' and isinstance(value, tuple):
                data.append((name, value))

            elif isinstance(value, basestring):
                data.append((name, value))

            else:
                data += [(name, v) for v in value]

        return data

    def html(self):
        """
        Return an HTML representation of the element
        """
        return lxml.html.tostring(self.element)

    def pretty(self):
        """
        Return an pretty-printed string representation of the element
        """
        return lxml.html.tostring(self.element, pretty_print=True)

    def striptags(self):
        """
        Strip tags out of ``lxml.html`` document ``node``, just leaving behind
        text. Normalize all sequences of whitespace to a single space.

        Use this for simple text comparisons when testing for document content

        Example::

            >>> from werkzeug import Response
            >>> myapp = Response(['<p>the <span>foo</span> is completely <strong>b</strong>azzed</p>'])
            >>> agent = TestAgent(myapp).get('/')
            >>> agent.one('//p').striptags()
            'the foo is completely bazzed'

        """
        def _striptags(node):
            if node.text:
                yield node.text
            for subnode in node:
                for text in _striptags(subnode):
                    yield text
            if node.tail:
                yield node.tail
        return re.sub(r'\s\s*', ' ', ''.join(_striptags(self.element)))

    def __contains__(self, what):
        return what in self.html()


class TestAgent(object):
    """
    A ``TestAgent`` object provides a user agent for the WSGI application under
    test.

    Key methods and properties:

        - ``get(path)``, ``post(path)``, ``post_multipart`` - create get/post
          requests for the WSGI application and return a new ``TestAgent`` object

        - ``request``, ``response`` - the `werkzeug` request and
          response objects associated with the last WSGI request.

        - ``body`` - the body response as a string

        - ``lxml`` - the lxml representation of the response body (only
           applicable for HTML responses)

        - ``reset()`` - reset the TestAgent object to its initial
           state, discarding any form field values

        - ``find()`` (or dictionary-style attribute access) - evalute the given
           xpath expression against the current response body and return a list.
    """

    response_class = Response
    _lxml= None

    environ_defaults = {
        'SCRIPT_NAME': "",
        'PATH_INFO': "",
        'QUERY_STRING': "",
        'SERVER_NAME': "localhost",
        'SERVER_PORT': "80",
        'SERVER_PROTOCOL': "HTTP/1.0",
        'REMOTE_ADDR': '127.0.0.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    def __init__(self, app, request=None, response=None, cookies=None, history=None, validate_wsgi=False):
        # TODO: Make validate_wsgi pass
        if validate_wsgi:
            app = wsgi_validator(app)
        self.app = app
        self.request = request
        self.response = response
        self._elements = []

        # Stores file upload field values in forms
        self.file_uploads = {}

        if cookies:
            self.cookies = cookies
        else:
            self.cookies = BaseCookie()
        if response:
            self.cookies.update(parse_cookies(response))
        if history:
            self.history = history
        else:
            self.history = []

    @classmethod
    def make_environ(cls, REQUEST_METHOD='GET', PATH_INFO='', wsgi_input='', **kwargs):
        SCRIPT_NAME = kwargs.pop('SCRIPT_NAME', cls.environ_defaults["SCRIPT_NAME"])

        if SCRIPT_NAME and SCRIPT_NAME[-1] == "/":
            SCRIPT_NAME = SCRIPT_NAME[:-1]
            PATH_INFO = "/" + PATH_INFO

        environ = cls.environ_defaults.copy()
        environ.update(kwargs)
        for key, value in kwargs.items():
            environ[key.replace('wsgi_', 'wsgi.')] = value

        if isinstance(wsgi_input, basestring):
            wsgi_input = StringIO(wsgi_input)

        environ.update({
            'REQUEST_METHOD': REQUEST_METHOD,
            'SCRIPT_NAME': SCRIPT_NAME,
            'PATH_INFO': PATH_INFO,
            'wsgi.input': wsgi_input,
            'wsgi.errors': StringIO(),
        })

        if environ['SCRIPT_NAME'] == '/':
            environ['SCRIPT_NAME'] = ''
            environ['PATH_INFO'] = '/' + environ['PATH_INFO']

        while PATH_INFO.startswith('//'):
            PATH_INFO = PATH_INFO[1:]

        return environ

    def _request(self, environ, follow=False, history=False):
        path = environ['SCRIPT_NAME'] + environ['PATH_INFO']
        environ['HTTP_COOKIE'] = '; '.join(
            '%s=%s' % (key, morsel.value)
            for key, morsel in self.cookies.items()
            if path.startswith(morsel['path'])
        )

        if '?' in environ['PATH_INFO']:
            environ['PATH_INFO'], querystring = environ['PATH_INFO'].split('?', 1)
            if environ.get('QUERY_STRING'):
                environ['QUERY_STRING'] += querystring
            else:
                environ['QUERY_STRING'] = querystring

        if history:
            history = self.history + [self]
        else:
            history = self.history

        response = self.response_class.from_app(self.app, environ)
        agent = self.__class__(self.app, Request(environ), response, self.cookies, history, validate_wsgi=False)
        if follow:
            return agent.follow_all()
        return agent

    def get(self, PATH_INFO='/', data=None, charset='UTF-8', follow=False, history=True, **kwargs):
        """
        Make a GET request to the application and return the response.
        """
        if data is not None:
            kwargs.setdefault('QUERY_STRING', werkzeug.url_encode(data, charset=charset, separator='&'))

        if self.request:
            PATH_INFO = uri_join_same_server(self.request.url, PATH_INFO)

        return self._request(
            self.make_environ('GET', PATH_INFO=PATH_INFO, **kwargs),
            follow,
            history,
        )

    def post(self, PATH_INFO='/', data=None, charset='UTF-8', follow=False, history=True, **kwargs):
        """
        Make a POST request to the application and return the response.
        """
        if data is None:
            data = []

        if self.request:
            PATH_INFO = uri_join_same_server(self.request.url, PATH_INFO)

        data = werkzeug.url_encode(data, charset=charset, separator='&')
        wsgi_input = StringIO(data)
        wsgi_input.seek(0)

        return self._request(
            self.make_environ(
                'POST', PATH_INFO=PATH_INFO,
                CONTENT_TYPE="application/x-www-form-urlencoded",
                CONTENT_LENGTH=str(len(data)),
                wsgi_input=wsgi_input,
                **kwargs
            ),
            follow,
            history,
        )

    def post_multipart(self, PATH_INFO='/', data=None, files=None, charset='UTF-8', follow=False, **kwargs):
        """
        Create a MockWSGI configured to post multipart/form-data to the given URI.

        This is usually used for mocking file uploads

        data
            dictionary of post data
        files
            list of ``(name, filename, content_type, data)`` tuples. ``data``
            may be either a byte string, iterator or file-like object.
        """

        if data is None:
            data = {}

        if files is None:
            files = []

        if self.request:
            PATH_INFO = uri_join_same_server(self.request.url, PATH_INFO)

        boundary = '----------------------------------------BoUnDaRyVaLuE'

        def add_headers(key, value):
            """
            Return a tuple of ``([(header-name, header-value), ...], data)``
            for the given key/value pair
            """
            if isinstance(value, tuple):
                filename, content_type, data = value
                headers = [
                    ('Content-Disposition',
                     'form-data; name="%s"; filename="%s"' % (key, filename)),
                    ('Content-Type', content_type)
                ]
                return headers, data
            else:
                if isinstance(value, unicode):
                    value = value.encode(charset)
                headers = [
                    ('Content-Disposition',
                    'form-data; name="%s"' % (key,))
                ]
                return headers, value

        items = chain(
            (add_headers(k, v) for k, v in data),
            (add_headers(k, (fname, ctype, data)) for k, fname, ctype, data in files),
        )

        CRLF = '\r\n'
        post_data = StringIO()
        post_data.write('--' + boundary)
        for headers, data in items:
            post_data.write(CRLF)
            for name, value in headers:
                post_data.write('%s: %s%s' % (name, value, CRLF))
            post_data.write(CRLF)
            if hasattr(data, 'read'):
                copyfileobj(data, post_data)
            elif isinstance(data, str):
                post_data.write(data)
            else:
                for chunk in data:
                    post_data.write(chunk)
            post_data.write(CRLF)
            post_data.write('--' + boundary)
        post_data.write('--' + CRLF)
        length = post_data.tell()
        post_data.seek(0)
        kwargs.setdefault('CONTENT_LENGTH', str(length))
        return self._request(
            self.make_environ(
                'POST',
                PATH_INFO,
                CONTENT_TYPE='multipart/form-data; boundary=%s' % boundary,
                wsgi_input=post_data,
                **kwargs
            ),
            follow=follow,
        )

    def start_response(self, status, headers, exc_info=None):
        """
        No-op implementation.
        """

    def __str__(self):
        if self.response:
            return str(self.response)
        else:
            return super(TestAgent, self).__str__()

    @property
    def body(self):
        return self.response.data

    @property
    def lxml(self):
        if self._lxml is not None:
            return self._lxml
        self.reset()
        return self._lxml

    @property
    def root_element(self):
        return ElementWrapper(self, self.lxml)

    def reset(self):
        """
        Reset the lxml document, abandoning any changes made
        """
        if not self.response:
            raise NoRequestMadeError
        for element in self._elements:
            element.reset()
        self._lxml = lxml.html.fromstring(self.response.data)

    def _find(self, path, namespaces=None, css=False, **kwargs):
        """
        Return elements matching the given xpath expression.

        For convenience that the EXSLT regular expression namespace
        (``http://exslt.org/regular-expressions``) is prebound to
        the prefix ``re``.
        """
        if css:
            selector = CSSSelector(path)
            return selector(self.lxml)

        ns = {'re': REGEXP_NAMESPACE}
        if namespaces is not None:
            ns.update(namespaces)
        namespaces = ns

        result = self.lxml.xpath(path, namespaces=namespaces, **kwargs)
        return result

    def one(self, path, css=False):
        """
        Returns the first result from Agent.all.  Raises an error if
        more than one result is found.
        """
        elements = self.all(path, css=css)
        if len(elements) > 1:
            raise MultipleMatchesError(path, elements)
        elif len(elements) == 0:
            raise NoMatchesError(path)
        else:
            return elements[0]

    def all(self, path, css=False):
        """
        Returns the results of Agent.find, or Agent._findcss if css is True
        """
        elements = self._find(path, css=css)
        return [ElementWrapper(self, el) for el in elements]

    def click(self, path, follow=False, **kwargs):
        return self.find(path, **kwargs).click(follow=follow)

    def _click(self, element, follow=False):
        return self.get(
            element.attrib['href'],
            follow=follow
        )

    def follow(self):
        """
        If response has a ``30x`` status code, fetch (``GET``) the redirect
        target. No entry is recorded in the agent's history list.
        """
        if not (300 <= int(self.response.status.split()[0]) < 400):
            raise AssertionError(
                "Can't follow non-redirect response (got %s for %s %s)" % (
                    self.response.status,
                    self.request.method,
                    self.request.path,
                )
            )

        return self.get(
            self.response.headers.get('Location'),
            history=False,
        )


    def follow_all(self):
        """
        If response has a ``30x`` status code, fetch (``GET``) the redirect
        target, until a non-redirect code is received. No entries are recorded
        in the agent's history list.
        """

        agent = self
        while True:
            try:
                agent = agent.follow()
            except AssertionError:
                return agent


    def back(self, count=1):
        return self.history[-abs(count)]

    def __enter__(self):
        """
        Provde support for context blocks
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        At end of context block, reset the lxml document
        """
        self.reset()

def uri_join_same_server(baseuri, uri):
    """
    Join two uris which are on the same server. The resulting URI will have the
    protocol and netloc portions removed. If the resulting URI has a different
    protocol/netloc then a ``ValueError`` will be raised.

        >>> uri_join_same_server('http://localhost/foo', 'bar')
        '/bar'
        >>> uri_join_same_server('http://localhost/foo', 'http://localhost/bar')
        '/bar'
        >>> uri_join_same_server('http://localhost/rhubarb/custard/', '../')
        '/rhubarb/'
        >>> uri_join_same_server('http://localhost/foo', 'http://example.org/bar')
        Traceback (most recent call last):
          ...
        ValueError: URI links to another server: http://example.org/bar

    """
    # TODO: Maybe rhubarb should have a trailing slash
    uri = urljoin(baseuri, uri)
    uri = urlparse(uri)
    if urlparse(baseuri)[:2] != uri[:2]:
        raise ValueError("URI links to another server: %s" % (urlunparse(uri),))
    return urlunparse((None, None) + uri[2:])

def parse_cookies(response):
    """
    Return a ``Cookie.BaseCookie`` object populated from cookies parsed from
    the response object
    """
    base_cookie = BaseCookie()
    for item in response.headers.get_all('Set-Cookie'):
        base_cookie.load(item)
    return base_cookie


